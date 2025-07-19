import requests
from celery import shared_task
from django.db import transaction
from dsp_integration.celery import app

from .models import DspEntityAudit, DspEntityQueue

API_BASE = "https://api.thirdpartydsp.com/v1"


@app.task(bind=True, max_retries=5)
def dave(self, queue_id):
    with transaction.atomic():
        # Get lock on the job within transaction block
        job = DspEntityQueue.objects.select_for_update().get(id=queue_id)
        job.attempts += 1
        job.status = "completed"
        job.save()


@app.task(bind=True, max_retries=5)
def submit_entity(self, queue_id):
    with transaction.atomic():
        # Get lock on the job within transaction block
        job = DspEntityQueue.objects.select_for_update().get(id=queue_id)

        if job.depends_on and job.depends_on.status != "completed":
            # release the lock and retry later
            raise self.retry(countdown=30)

        job.attempts += 1
        job.save()

        try:
            resp = requests.post(f"{API_BASE}/{job.entity_type}", json=job.payload)
            DspEntityAudit.objects.create(
                queue=job,
                http_status=resp.status_code,
                response=resp.json(),
                backoff_secs=self.request.delivery_info.get("countdown", 0),
            )
            job.status = "submitted" if resp.status_code == 202 else "pending"
            job.save()
            if resp.status_code != 202:
                raise Exception("Unexpected status")
        except Exception as exc:
            job.last_error = str(exc)
            job.save()
            raise self.retry(exc=exc, countdown=self.request.retries * 60)


# @shared_task
@app.task(bind=True, max_retries=5)
def poll_submissions():
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
            if data.get("status") == "success":
                job.status = "completed"
            elif data.get("status") == "failed":
                job.status = "failed"
                job.last_error = data.get("error_message")
            job.save()
        except requests.RequestException as exc:
            job.last_error = str(exc)
            job.save()
