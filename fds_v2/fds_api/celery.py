import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fds_api.settings")

app = Celery("fds_api")

# Read CELERY_* settings from Django settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in installed apps
app.autodiscover_tasks()