"""
Celery application factory.
Keep this file lightweight - just define the Celery app without complex imports.
"""
from celery import Celery
import os


def create_celery_app():
    """Factory function to create a properly configured Celery instance"""
    _app = Celery(
        'app',
        broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
        backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    )

    # Configure Celery
    _app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_always_eager=False,  # Set to True for testing/debugging
        worker_prefetch_multiplier=1,  # Prevents worker from prefetching too many tasks
        task_acks_late=True,  # Tasks are acknowledged after execution
        task_reject_on_worker_lost=True,  # Tasks are requeued if worker is lost
        broker_connection_retry=True,  # Retry connecting to broker
        broker_connection_retry_on_startup=True,  # Retry connecting on startup
        broker_connection_max_retries=10,  # Maximum number of retries
    )

    return _app


# Create the Celery app instance
celery_app = create_celery_app()


# This function allows FastAPI to share the same Celery instance
def get_celery_app():
    return celery_app
