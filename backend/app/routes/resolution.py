"""
Resolution Status Endpoint - Monitor prediction resolution background task
"""

from fastapi import APIRouter, Depends, HTTPException
from app.services.prediction_resolution_service import PredictionResolutionService
from app.services.auth_service import get_current_user
from app.models.db_models import User
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resolution", tags=["resolution"])

# Global instance for tracking stats
_resolution_service: PredictionResolutionService | None = None

class ResolutionStatusResponse(BaseModel):
    status: str
    stats: Dict[str, Any]
    description: str

class ResolutionTriggerResponse(BaseModel):
    message: str
    resolved_count: int
    errors: int
    duration_seconds: float

def get_resolution_service() -> PredictionResolutionService:
    """Get or initialize resolution service"""
    global _resolution_service
    if _resolution_service is None:
        _resolution_service = PredictionResolutionService()
    return _resolution_service


@router.get("/status", response_model=ResolutionStatusResponse)
async def get_resolution_status():
    """Get prediction resolution background task status (public endpoint)"""
    service = get_resolution_service()
    stats = await service.get_stats()
    return ResolutionStatusResponse(
        status='active',
        stats=stats,
        description='Predictions are being resolved automatically every hour'
    )


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Restrict endpoint to admin-tier users only."""
    if getattr(current_user, "subscription_tier", None) != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.post("/trigger", response_model=ResolutionTriggerResponse, dependencies=[Depends(require_admin)])
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
        return ResolutionTriggerResponse(
            message="Resolution completed successfully",
            resolved_count=result.get("resolved", 0),
            errors=result.get("errors", 0),
            duration_seconds=result.get("duration", 0.0)
        )
    except Exception as e:
        logger.error(f"❌ Error during manual resolution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Resolution failed: {str(e)}")
