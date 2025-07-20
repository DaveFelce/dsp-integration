import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dsp_integration.settings")
app = Celery("dsp_integration")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
