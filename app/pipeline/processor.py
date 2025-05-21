import os
from datetime import datetime

from app.models.track import AnalyticsTrackBase
from app.pipeline.celery_config import celery_app
from app.core.db import engine
from app.queries.track import select_un_processed_analytics
from sqlmodel import create_engine, Session
from celery.utils.log import get_task_logger

from app.services.amplitude import AmplitudeTracker

# analytics_data = Table('analyticstrackbase', metadata, autoload_with=engine)
logger = get_task_logger(__name__)
DEBUG_CELERY = os.environ.get('DEBUG_CELERY', 'False').lower() == 'true'

session = Session(engine)


# @celery_app.task()
@celery_app.task()
def process_analytics_batch(batch_size=1000):
    """
    Process a batch of unprocessed analytics data rows.
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Starting analytics batch processing with size {batch_size}")

    try:
        # Find unprocessed records (those with processed_at = NULL)
        rows = select_un_processed_analytics(query_size=batch_size, session=session)

        if not rows:
            logger.info("No unprocessed rows found")
            return {"status": "success", "rows_processed": 0, "message": "No unprocessed rows found"}

        logger.info(f"Found {len(rows)} unprocessed analytics rows")

        # Debug first row to understand structure
        if rows:
            try:
                sample_data = rows[0]
                logger.debug(f"Sample row: id={getattr(sample_data, 'id', None)}, "
                             f"event_name={getattr(sample_data, 'event_name', None)}")

                # Check if events have the required fields
                missing_event_name = sum(1 for r in rows if not getattr(r, 'event_name', None))
                if missing_event_name:
                    logger.warning(f"{missing_event_name} rows missing event_name field")
            except Exception as e:
                logger.error(f"Error examining rows: {str(e)}")

        processed_ids = []

        try:
            # Initialize Amplitude tracker
            amplitude = AmplitudeTracker()
            logger.info("AmplitudeTracker initialized")

            # Track events batch - with explicit error handling
            track_success = amplitude.track_events(events=rows)

            if not track_success:
                logger.error("Failed to track events in Amplitude")
                raise Exception("Amplitude tracking failed")

            logger.info("Successfully tracked events in Amplitude")

            # Flush events with explicit error handling
            flush_success = amplitude.flush()

            if not flush_success:
                logger.error("Failed to flush events to Amplitude")
                raise Exception("Amplitude flush failed")

            logger.info("Successfully flushed events to Amplitude")

            # If we got here, both tracking and flushing succeeded
            for row in rows:
                processed_ids.append(row.id)
        except Exception as e:
            logger.error(f"Amplitude processing error: {str(e)}", exc_info=True)
            raise  # Re-raise to trigger retry

        # Update processed status
        now = datetime.utcnow()

        logger.info(f"Marking {len(processed_ids)} rows as processed")

        if processed_ids:
            try:
                # session.query(AnalyticsTrackBase).filter(AnalyticsTrackBase.id.in_(processed_ids)).update(
                #     {"processed_at": now}, synchronize_session='fetch')
                # session.commit()
                logger.info(f"Successfully processed {len(processed_ids)} rows")
            except Exception as db_error:
                logger.error(f"Database error updating processed status: {str(db_error)}", exc_info=True)
                session.rollback()
                raise

        return {
            "status": "success",
            "rows_processed": len(processed_ids),
            "processed_at": now.isoformat() if processed_ids else None
        }

    except Exception as e:
        session.rollback()
        logger.error(f"Error in analytics processing: {str(e)}", exc_info=True)
        # Retry the task on failure
        return {"status": "error", "message": str(e)}

    finally:
        logger.debug("Closing database session")
        session.close()


# @celery_app.task()
# def trigger_analytics_processing(batch_size=1000):
#     """manually trigger"""
#     with open("my_file.txt", "a") as file:
#         file.write("This line is appended.\n")
#     return process_analytics_batch.delay(batch_size=batch_size)


@celery_app.task()
def trigger_analytics_processing(batch_size=1000):
    """Manually trigger analytics processing"""
    logger.info(f"Manually triggering analytics processing with batch size {batch_size}")

    # return process_analytics_batch(batch_size=batch_size)
    process_analytics_batch.delay(batch_size=batch_size)
    return {"status": "success"}
