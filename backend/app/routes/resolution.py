"""
Resolution Status Endpoint - Monitor prediction resolution background task
"""

from fastapi import APIRouter, Depends, HTTPException
from app.services.prediction_resolution_service import PredictionResolutionService
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resolution", tags=["resolution"])

# Global instance for tracking stats
_resolution_service: PredictionResolutionService | None = None

def get_resolution_service() -> PredictionResolutionService:
    """Get or initialize resolution service"""
    global _resolution_service
    if _resolution_service is None:
        _resolution_service = PredictionResolutionService()
    return _resolution_service


@router.get("/status")
async def get_resolution_status():
    """Get prediction resolution background task status (public endpoint)"""
    service = get_resolution_service()
    stats = await service.get_stats()
    return {
        'status': 'active',
        'stats': stats,
        'description': 'Predictions are being resolved automatically every hour'
    }


@router.post("/trigger")
async def trigger_resolution_manually(db: AsyncSession = Depends(get_db)):
    """
    Manually trigger prediction resolution task for debugging/testing.
    This resolves all pending predictions that have completed games.
    """
    try:
        logger.info("🚀 Manual resolution trigger called")
        service = get_resolution_service()
        result = await service.resolve_all_pending_predictions(db)
        logger.info(f"✅ Manual resolution completed: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Error during manual resolution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Resolution failed: {str(e)}")
