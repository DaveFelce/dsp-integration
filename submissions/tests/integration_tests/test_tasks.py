from http import HTTPStatus

import pytest
import responses
from submissions.models import DspEntityAudit, DspEntityQueue
from submissions.tasks import API_BASE, submit_entity


@pytest.mark.django_db
@responses.activate
def test_submit_entity_happy_path_using_responses() -> None:
    # Arrange
    # Create a pending job
    job = DspEntityQueue.objects.create(
        entity_type="campaign",
        payload={"name": "Unit Test Campaign", "budget": 123},
        status=DspEntityQueue.Status.PENDING,
    )

    # Mock the POST endpoint to return 202 Accepted
    url = f"{API_BASE}/{job.entity_type}"
    responses.add(responses.POST, url, json={"result": "accepted"}, status=HTTPStatus.ACCEPTED)

    # Act
    # Run the task synchronously (no broker needed)
    submit_entity.run(job.id)

    # Refresh from DB and assert status change
    job.refresh_from_db()
    assert job.status == DspEntityQueue.Status.SUBMITTED

    # Assert
    # Assert that an audit record was created
    audit = DspEntityAudit.objects.get(queue=job)
    assert audit.http_status == HTTPStatus.ACCEPTED
    assert audit.response == {"result": "accepted"}
