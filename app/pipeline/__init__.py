"""
Import all modules here to ensure tasks are registered properly.
"""
# Import these modules to ensure tasks are registered properly when Celery starts
from app.pipeline.celery_app import celery_app, get_celery_app
from app.pipeline.processor import process_analytics_batch, trigger_analytics_processing

# This makes tasks available at top level, e.g., from app.celery import trigger_analytics_processing
__all__ = ['celery_app', 'get_celery_app', 'process_analytics_batch', 'trigger_analytics_processing']
