import pytest
import requests
from submissions.models import DspEntityQueue, DspEntityAudit
from submissions.tasks import submit_entity

@pytest.mark.django_db  # enable DB for this test
def test_submit_entity_test():
    assert True

@pytest.mark.django_db  # enable DB for this test
def test_submit_entity_happy_path(monkeypatch):
    # 1. Create a pending job
    job = DspEntityQueue.objects.create(
        entity_type='campaign',
        payload={'name': 'Unit Test Campaign', 'budget': 123},
        status=DspEntityQueue.Status.PENDING,  # use the TextChoices enum
    )

    # 2. Mock requests.post to simulate a 202 Accepted response
    class FakeResponse:
        status_code = 202

        def json(self):
            return {'result': 'accepted'}

    monkeypatch.setattr(requests, 'post', lambda url, json: FakeResponse())

    # 3. Run the task synchronously (no broker needed)
    #    .run() calls the task code directly with `self` bound to the Task instance
    submit_entity.run(job.id)

    # 4. Refresh from DB and assert status change
    job.refresh_from_db()
    assert job.status == DspEntityQueue.Status.SUBMITTED

    # 5. Assert that an audit entry was created with the correct HTTP status
    audit = DspEntityAudit.objects.get(queue=job)
    assert audit.http_status == 202
    assert audit.response == {'result': 'accepted'}