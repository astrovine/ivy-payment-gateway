from celery import Celery
import os

from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

BROKER_URL = os.getenv("CELERY_BROKER_URL") or os.getenv("REDIS_URL", "redis://redis:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND") or os.getenv("REDIS_URL", BROKER_URL)


DEFAULT_BEAT_SCHEDULE_FILE = os.getenv("CELERY_BEAT_SCHEDULE", "/tmp/celerybeat-schedule")

celery_app = Celery(
    "payment_gateway",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
)

celery_app.conf.beat_schedule = {
    "settle_pending_funds_at":{
        "task": "app.tasks.settle_pending_funds_task",
        'schedule': crontab(hour=0, minute=5),
    },
}


celery_app.conf.beat_schedule_filename = DEFAULT_BEAT_SCHEDULE_FILE

celery_app.conf.update(schedule_filename=DEFAULT_BEAT_SCHEDULE_FILE)

celery_app.autodiscover_tasks(["app"])

IS_PYTEST = "PYTEST_CURRENT_TEST" in os.environ
TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true"
if IS_PYTEST or TASK_ALWAYS_EAGER:
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        result_backend=None,
    )
else:
    celery_app.conf.update(
        task_track_started=True,
    )
