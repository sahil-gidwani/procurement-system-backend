import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "procurement_system_backend.settings")

app = Celery("procurement_system_backend")

app.conf.enable_utc = False
app.conf.update(timezone="Asia/Kolkata")
app.config_from_object("django.conf:settings", namespace="CELERY")

# Celery Beat Schedule
app.conf.beat_schedule = {
    "send-inventory-notifications": {
        "task": "inventory.tasks.send_inventory_notifications",
        "schedule": crontab(hour=10, minute=0, day_of_week=1),
    },
}

app.autodiscover_tasks()
