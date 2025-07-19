from django.db import models


class DspEntityQueue(models.Model):
    class Status(models.TextChoices):
        WAITING = "waiting", "Waiting"
        PENDING = "pending", "Pending"
        SUBMITTED = "submitted", "Submitted"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    entity_type = models.CharField(max_length=50)
    payload = models.JSONField()
    depends_on = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT)
    # status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.WAITING,
    )
    attempts = models.IntegerField(default=0)
    last_error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# For future development
class DspEntityAudit(models.Model):
    queue = models.ForeignKey(DspEntityQueue, related_name="audits", on_delete=models.CASCADE)
    attempt_at = models.DateTimeField(auto_now_add=True)
    http_status = models.IntegerField(null=True)
    response = models.JSONField(null=True)
    backoff_secs = models.IntegerField(default=0)
