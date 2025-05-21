from celery import Celery
from celery.schedules import crontab
import os
import redis

# Create Celery instance
celery_app = None
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
try:
    redis.Redis(host='localhost', port=6379).ping()
    celery_app = Celery(
        'app',
        broker=CELERY_BROKER_URL,
        backend=CELERY_RESULT_BACKEND
    )
except redis.exceptions.ConnectionError:
    print("Unable to connect to the Redis server. Exiting...")
    exit()

if celery_app is not None:
    print("Registered tasks:", celery_app.tasks.keys())
    # Configure Celery
    celery_app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_acks_late=True,  # Only acknowledge task after it's been executed
        task_reject_on_worker_lost=True,  # Reject tasks if worker crashes
        worker_prefetch_multiplier=1,  # Don't prefetch more tasks than can be processed
        task_track_started=True,  # Mark tasks as started when they start running
    )

    # Set up task imports explicitly
    celery_app.conf.imports = ('app.pipeline.processor',)
    # Define periodic tasks
    celery_app.conf.beat_schedule = {
        'process-analytics-data-every-minute': {
            'task': 'app.pipeline.processor.process_analytics_batch',
            'schedule': crontab(minute="*/1"),
            'kwargs': {'batch_size': 1000},
        }
    }

    # Auto-discover tasks
    celery_app.autodiscover_tasks(['app.pipeline'])
    print("Beat schedule:", celery_app.conf.beat_schedule)
    print("Registered tasks:", celery_app.tasks.keys())
