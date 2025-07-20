#!/usr/bin/env python
"""
Simulates a production service creating a DSP entity and enqueuing
the Celery task to submit it to the third‐party API, using logging.
"""

import logging
import os

import django

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Point at the Django settings and bootstrap
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dsp_integration.settings")
django.setup()

from submissions.models import DspEntityQueue
from submissions.tasks import mock_submit_entity_success


def main():
    # Example payload for a 'campaign' entity
    payload = {
        "name": "Summer Promo 2025",
        "budget": 5000,
        "start_date": "2025-08-01",
        "end_date": "2025-08-31",
    }

    try:
        # Create the queue entry using the Status enum
        job = DspEntityQueue.objects.create(
            entity_type="campaign",
            payload=payload,
            status=DspEntityQueue.Status.PENDING,  # using TextChoices
        )
        logger.info("Created job ID=%s with status=%s", job.id, job.status)

        # Enqueue the Celery task
        result = mock_submit_entity_success.delay(job.id)
        logger.info("Task enqueued: task_id=%s", result.id)

        task_output = result.get(timeout=30)  # may raise on timeout or failure
        logger.info("Task completed successfully: %r", task_output)

    except Exception as exc:
        # Catch any error in submission or waiting
        logger.error("Error during simulate_submission: %s", exc, exc_info=True)


if __name__ == "__main__":
    main()
