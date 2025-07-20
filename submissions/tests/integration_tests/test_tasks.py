# tests/test_tasks.py

import pytest
import responses
from django.urls import reverse

from submissions.models import DspEntityQueue, DspEntityAudit
from submissions.tasks import submit_entity

API_BASE = "https://api.thirdpartydsp.com/v1"


@pytest.mark.django_db
@responses.activate
def test_submit_entity_happy_path_using_responses():
    # 1. Create a pending job
    job = DspEntityQueue.objects.create(
        entity_type="campaign",
        payload={"name": "Unit Test Campaign", "budget": 123},
        status=DspEntityQueue.Status.PENDING,
    )

    # 2. Mock the POST endpoint to return 202 Accepted
    url = f"{API_BASE}/{job.entity_type}"
    responses.add(responses.POST, url, json={"result": "accepted"}, status=202)

    # 3. Run the task synchronously (no broker needed)
    submit_entity.run(job.id)

    # 4. Refresh from DB and assert status change
    job.refresh_from_db()
    assert job.status == DspEntityQueue.Status.SUBMITTED

    # 5. Assert an audit record was created
    audit = DspEntityAudit.objects.get(queue=job)
    assert audit.http_status == 202
    assert audit.response == {"result": "accepted"}
