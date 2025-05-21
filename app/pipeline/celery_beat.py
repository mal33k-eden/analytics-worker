"""
Celery beat schedule configuration.
This is separate from tasks to prevent circular imports.
"""
from celery.schedules import crontab
from app.pipeline.celery_app import celery_app

# Configure beat schedule
celery_app.conf.beat_schedule = {
    'process-analytics-data-every-minute': {
        'task': 'app.pipeline.processor.process_analytics_batch',
        'schedule': crontab(minute="*/1"),
        'options': {
            'queue': 'analytics',
            'expires': 60 * 2,  # Task expires after 2 minutes
        }
    },
}
