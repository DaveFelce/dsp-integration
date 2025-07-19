from celery import shared_task
import requests
from .models import DspEntityQueue, DspEntityAudit

API_BASE = 'https://api.thirdpartydsp.com/v1'

@shared_task(bind=True, max_retries=5)
def submit_entity(self, queue_id):
    job = DspEntityQueue.objects.select_for_update().get(id=queue_id)
    if job.depends_on and job.depends_on.status != 'completed':
        raise self.retry(countdown=30)
    try:
        resp = requests.post(f"{API_BASE}/{job.entity_type}", json=job.payload)
        job.attempts += 1
        DspEntityAudit.objects.create(
            queue=job,
            http_status=resp.status_code,
            response=resp.json(),
            backoff_secs=self.request.delivery_info.get('countdown', 0),
        )
        if resp.status_code == 202:
            job.status = 'submitted'
        else:
            job.status = 'pending'
            job.save()
            raise Exception('Unexpected status')
    except Exception as exc:
        job.last_error = str(exc)
        job.save()
        raise self.retry(exc=exc, countdown=self.request.retries * 60)
    else:
        job.save()

@shared_task
def poll_submissions():
    pending = DspEntityQueue.objects.filter(status='submitted')
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
            if data.get('status') == 'success':
                job.status = 'completed'
            elif data.get('status') == 'failed':
                job.status = 'failed'
                job.last_error = data.get('error_message')
            job.save()
        except requests.RequestException as exc:
            job.last_error = str(exc)
            job.save()
