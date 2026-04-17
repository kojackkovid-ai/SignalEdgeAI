from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth_service import AuthService
from app.services.prediction_service import PredictionService
from app.models.db_models import user_predictions
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Singleton instances - created once and reused across all requests
_auth_service_instance = None
_prediction_service_instance = None

# Dependency functions for service injection
def get_auth_service() -> AuthService:
    """Get or create AuthService instance (singleton)"""
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = AuthService()
    return _auth_service_instance

def get_prediction_service() -> PredictionService:
    """Get or create PredictionService instance (singleton)"""
    global _prediction_service_instance
    if _prediction_service_instance is None:
        _prediction_service_instance = PredictionService()
    return _prediction_service_instance

async def get_current_user(authorization: Optional[str] = Header(None, description="Bearer token")) -> str:
    """Extract user ID from Bearer token in Authorization header"""
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    auth_service = AuthService()
    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
        return auth_service._decode_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )


router = APIRouter()

class UserProfileResponse(BaseModel):
    id: str
    email: str
    username: str
    subscription_tier: str
    created_at: str
    win_rate: float
    total_predictions: int
    roi: float

class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None
    preferences: Optional[dict] = None

@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile"""
    user = await get_auth_service().get_user_by_id(db, current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "subscription_tier": user.subscription_tier,
        "created_at": user.created_at.isoformat(),
        "win_rate": user.win_rate or 0.0,
        "total_predictions": user.total_predictions or 0,
        "roi": user.roi or 0.0
    }

@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get user profile by ID"""
    user = await get_auth_service().get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "subscription_tier": user.subscription_tier,
        "created_at": user.created_at.isoformat(),
        "win_rate": user.win_rate or 0.0,
        "total_predictions": user.total_predictions or 0,
        "roi": user.roi or 0.0
    }

@router.put("/me")
async def update_profile(
    request: UpdateProfileRequest,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile"""
    user = await get_auth_service().get_user_by_id(db, current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if request.username:
        user.username = request.username
    if request.preferences:
        user.preferences = request.preferences
    
    await db.commit()
    return {"message": "Profile updated successfully"}

class UpgradeRequest(BaseModel):
    new_tier: str
    billing_cycle: str
    amount: float

@router.post("/upgrade")
async def upgrade_subscription(
    request: UpgradeRequest,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upgrade user subscription tier after payment"""
    try:
        # Validate tier
        valid_tiers = ['basic', 'pro', 'elite']
        if request.new_tier not in valid_tiers:
            raise HTTPException(status_code=400, detail="Invalid tier")
        
        # Get user
        user = await get_auth_service().get_user_by_id(db, current_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # TODO: Verify payment with Stripe/payment processor
        # payment_verified = verify_payment(request.amount, ...)
        
        # Update user tier
        user.subscription_tier = request.new_tier
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"User {current_user_id} upgraded to {request.new_tier}")
        
        return {
            "message": "Subscription upgraded successfully",
            "new_tier": user.subscription_tier
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error upgrading subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_user_stats(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user statistics (win rate, predictions, average confidence, ROI)"""
    
    try:
        from sqlalchemy import select, func as sa_func
        from app.models.db_models import Prediction
        
        user = await get_auth_service().get_user_by_id(db, current_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Calculate total predictions from database (fresh count, not just model field)
        # EXCLUDE Club 100 access picks (sport='club_100_access')
        total_predictions_result = await db.execute(
            select(sa_func.count(Prediction.id))
            .where(
                Prediction.id.in_(
                    select(user_predictions.c.prediction_id)
                    .where(user_predictions.c.user_id == current_user_id)
                ),
                Prediction.sport != 'club_100_access'
            )
        )
        total_predictions = total_predictions_result.scalar() or 0
        
        # Calculate average confidence from user's predictions
        # IMPORTANT: Confidence stored as 0-100; normalize to 0-1 for API
        # EXCLUDE Club 100 access picks (sport='club_100_access')
        avg_confidence = 0.0
        try:
            result = await db.execute(
                select(sa_func.avg(Prediction.confidence))
                .where(
                    Prediction.id.in_(
                        select(user_predictions.c.prediction_id)
                        .where(user_predictions.c.user_id == current_user_id)
                    ),
                    Prediction.sport != 'club_100_access'
                )
            )
            avg_confidence_val = result.scalar()
            if avg_confidence_val is not None:
                avg_confidence = float(avg_confidence_val)
                # Normalize from 0-100 to 0-1 if value is > 1
                if avg_confidence > 1.0:
                    avg_confidence = avg_confidence / 100.0
        except Exception as e:
            logger.warning(f"Error calculating average confidence: {e}")
            avg_confidence = 0.0
        
        # Get tier config for dynamic daily picks limit
        from app.models.tier_features import TierFeatures
        tier_name = user.subscription_tier or 'starter'
        tier_config = TierFeatures.get_tier_config(tier_name)
        daily_picks_limit = tier_config.get('predictions_per_day', 1) if tier_config else 1
        
        return {
            "win_rate": user.win_rate or 0.0,
            "total_predictions": total_predictions,
            "avg_confidence": avg_confidence,  # Changed from profit_loss to avg_confidence
            "roi": user.roi or 0.0,
            "subscription_tier": user.subscription_tier or 'starter',
            "daily_picks_used": 0,  # Will be calculated separately
            "daily_picks_limit": daily_picks_limit   # Now using tier config
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tier")
async def get_user_tier(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user tier information with daily limits"""
    
    try:
        # Get user
        user = await get_auth_service().get_user_by_id(db, current_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # DEBUG: Log the raw tier value from database
        raw_tier = user.subscription_tier
        logger.info(f"[TIER DEBUG] User {current_user_id} - Raw subscription_tier from DB: '{raw_tier}'")
        logger.info(f"[TIER DEBUG] Tier type: {type(raw_tier)}, repr: {repr(raw_tier)}")
        
        # Get daily picks count
        prediction_service = get_prediction_service()
        picks_used = await prediction_service.get_daily_picks_count(db, current_user_id)
        
        # Tier-based daily limits - using tier_features.py configuration
        from app.models.tier_features import TierFeatures
        tier_limits = {}
        for tier_name in TierFeatures.all_tiers():
            tier_config = TierFeatures.get_tier_config(tier_name)
            if tier_config:
                tier_limits[tier_name] = tier_config.get('predictions_per_day', 1)
        
        # Add deprecated tier names for backwards compatibility
        tier_limits.update({
            'free': 1,
            'trial': 5
        })
        
        # Robust tier normalization - handle all possible formats
        if raw_tier:
            normalized_tier = str(raw_tier).lower().strip().replace('\\', '').replace('"', '').replace("'", '')
        else:
            normalized_tier = 'starter'
        
        # Handle case where tier might be stored with extra characters
        normalized_tier = normalized_tier.split(',')[0].strip() if ',' in normalized_tier else normalized_tier
        
        daily_limit = tier_limits.get(normalized_tier, 1)
        
        # Force unlimited tiers to have 9999 daily limit
        if normalized_tier in ['elite', 'pro_plus']:
            daily_limit = 9999
            logger.info(f"[TIER DEBUG] {normalized_tier.upper()} USER DETECTED - Setting daily limit to 9999 (unlimited)")
        
        # DEBUG: Log the normalized tier and limit
        logger.info(f"[TIER DEBUG] User {current_user_id} - Normalized tier: '{normalized_tier}', Daily limit: {daily_limit}")
        
        return {
            "tier": normalized_tier,
            "daily_limit": daily_limit,
            "picks_used_today": picks_used,
            "picks_remaining": daily_limit - picks_used,
            "features": {
                "show_odds": normalized_tier in ['basic', 'pro', 'pro_plus', 'elite'],
                "show_reasoning": normalized_tier in ['basic', 'pro', 'pro_plus', 'elite'],
                "show_models": normalized_tier in ['pro', 'pro_plus', 'elite'],
                "show_line": normalized_tier in ['basic', 'pro', 'pro_plus', 'elite'],
                "ai_breakdown": normalized_tier in ['pro_plus', 'elite'],
                "unlimited_picks": normalized_tier in ['pro_plus', 'elite']
            },
            "is_unlimited": normalized_tier in ['elite', 'pro_plus']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TIER DEBUG] Error in get_user_tier: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
