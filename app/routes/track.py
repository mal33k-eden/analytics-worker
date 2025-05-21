import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.deps import AsyncSession
from app.models.track import AnalyticsTrackBase
from app.pipeline.processor import trigger_analytics_processing, process_analytics_batch

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["track"])


@router.post("/track")
async def receive_analytics_to_queue(analytics: AnalyticsTrackBase,
                                     session: AsyncSession) -> Any:
    """"
            {
          "event_id": "072967b0-451e-454e-8023-5366c6fd31c6",
          "app_id": "esa",
          "event_name": "cart_add",
          "event_data": {
            "cart_id": 11,
            "account_id": 23456789
          },
          "identity": {
            "amplitude": {
              "device_id": "e3c794c0-6313-48f0-bed2-4dd59b8f12df"
            }
          },
          "metadata": {}
        }
    """
    analytics_item = analytics
    session.add(analytics_item)
    session.commit()
    session.refresh(analytics_item)
    return JSONResponse(content={"status": "all done"}, status_code=200)


@router.post("/analytics/process/")
async def manual_process_analytics(batch_size: int = 1000):
    task = trigger_analytics_processing(batch_size=batch_size)
    return {"task_id": "task.id", "status": "processing"}


@router.post("/api/trigger-analytics")
async def trigger_analytics(request: Request, batch_size: int = 1000):
    """
    Manually trigger analytics processing
    """
    try:
        task = process_analytics_batch.delay(batch_size=batch_size)

        return {
            "status": "success",
            "message": "Analytics processing triggered",
            "task_id": task.id
        }

    except Exception as e:
        logger.error(f"Failed to trigger analytics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger analytics processing: {str(e)}"
        )
