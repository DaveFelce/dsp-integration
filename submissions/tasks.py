import requests
from celery import Task
from django.db import transaction
from dsp_integration.celery import app

from .models import DspEntityAudit, DspEntityQueue

API_BASE = "https://api.thirdpartydsp.com/v1"


# @app.task(bind=True, max_retries=5)
# def dave(self, queue_id):
#     with transaction.atomic():
#         # Get lock on the job within transaction block
#         job = DspEntityQueue.objects.select_for_update().get(id=queue_id)
#         job.attempts += 1
#         job.status = DspEntityQueue.Status.FAILED
#         job.save()
#
#         return {"queue_id": queue_id, "status": job.status}
class BaseTaskWithRetry(Task):
    autoretry_for = (requests.RequestException,)
    max_retries = 5
    retry_backoff = True
    retry_backoff_max = 200
    retry_jitter = True


@app.task(bind=True, base=BaseTaskWithRetry)
def submit_entity(self, queue_id):
    with transaction.atomic():
        # Get lock on the job within transaction block
        job = DspEntityQueue.objects.select_for_update().get(id=queue_id)

        if job.depends_on and job.depends_on.status != DspEntityQueue.Status.COMPLETED:
            # release the lock and retry later
            raise self.retry(countdown=30)

        job.attempts += 1
        job.save()

        try:
            resp = requests.post(f"{API_BASE}/{job.entity_type}", json=job.payload)
            resp.raise_for_status()

            DspEntityAudit.objects.create(
                queue=job,
                http_status=resp.status_code,
                response=resp.json(),
                backoff_secs=self.request.delivery_info.get("countdown", 0),
            )

            if resp.status_code == 202:
                job.status = DspEntityQueue.Status.SUBMITTED
                job.save()
            else:
                job.status = DspEntityQueue.Status.PENDING
                job.save()
                raise requests.HTTPError(f"Expected status 202, got {resp.status_code}")
        except requests.RequestException as exc:
            job.last_error = str(exc)
            job.save()
            raise self.retry(exc=exc, countdown=self.request.retries * 60)


# For future development: this task polls the status of submitted jobs
@app.task(bind=True, max_retries=5)
def poll_submissions():
    # TODO: Use the Status enum from the model
    pending = DspEntityQueue.objects.filter(status="submitted")
    for job in pending:
        try:
            resp = requests.get(f"{API_BASE}/{job.entity_type}/{job.id}/status")
            DspEntityAudit.objects.create(
                queue=job,
                http_status=resp.status_code,
                response=resp.json(),
                backoff_secs=0,
            )
            data = resp.json()
            # TODO: use the Status enum from the model
            if data.get("status") == "success":
                job.status = "completed"
            elif data.get("status") == "failed":
                job.status = "failed"
                job.last_error = data.get("error_message")
            job.save()
        except requests.RequestException as exc:
            job.last_error = str(exc)
            job.save()
