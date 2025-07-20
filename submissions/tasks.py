from http import HTTPStatus

import requests
from celery import Task
from django.db import transaction
from dsp_integration.celery import app

from .models import DspEntityAudit, DspEntityQueue

API_BASE = "https://api.thirdpartydsp.com/v1"


class BaseTaskWithRetry(Task):
    autoretry_for = (requests.RequestException,)
    max_retries = 5
    retry_backoff = True
    retry_backoff_max = 200
    retry_jitter = True


@app.task(bind=True, base=BaseTaskWithRetry)
def mock_submit_entity_success(self, queue_id: int) -> dict:
    with transaction.atomic():
        # Get lock on the job within transaction block
        job = DspEntityQueue.objects.select_for_update().get(id=queue_id)
        job.attempts += 1
        job.status = DspEntityQueue.Status.SUBMITTED
        job.save()

        mock_response_json = {"queue_id": queue_id, "status": job.status}

        DspEntityAudit.objects.create(
            queue=job,
            http_status=HTTPStatus.ACCEPTED,
            response=mock_response_json,
        )

        return mock_response_json


@app.task(bind=True, base=BaseTaskWithRetry)
def submit_entity(self, queue_id: int) -> dict:
    with transaction.atomic():
        # Get lock on the job within transaction block
        job = DspEntityQueue.objects.select_for_update().get(id=queue_id)

        if job.depends_on and job.depends_on.status != DspEntityQueue.Status.COMPLETED:
            # release the lock and retry later
            raise self.retry(countdown=30)  # 30 seconds delay should be in config, not hardcoded

        job.attempts += 1
        job.save()

        try:
            resp = requests.post(f"{API_BASE}/{job.entity_type}", json=job.payload)
            resp.raise_for_status()

            DspEntityAudit.objects.create(
                queue=job,
                http_status=resp.status_code,
                response=resp.json(),
            )

            if resp.status_code == HTTPStatus.ACCEPTED:
                job.status = DspEntityQueue.Status.SUBMITTED
                job.save()

                return resp.json()
            else:
                job.status = DspEntityQueue.Status.PENDING
                job.save()
                raise requests.HTTPError(f"Expected status {HTTPStatus.ACCEPTED}, got {resp.status_code}")

        except requests.RequestException as exc:
            job.last_error = str(exc)
            job.save()
            raise self.retry(exc=exc)


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
