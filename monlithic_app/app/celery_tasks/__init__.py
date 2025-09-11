from celery import Celery
from ..config.settings import settings

# Create Celery app
celery_app = Celery(
    "blinkit_clone",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['app.celery_tasks.tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=60,  # 1 minute
)