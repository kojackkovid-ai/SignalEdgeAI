"""
Integration examples showing how to use the new features
Copy these patterns into your route handlers
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.requests import (
    PredictionFilterRequest, 
    FollowPredictionRequest,
    LoginRequest,
    RegisterRequest,
    PlayerPropsFilterRequest
)
from app.models.responses import (
    SuccessResponse, 
    ErrorResponse,
    PaginatedResponse,
    PredictionNotFoundError,
    InvalidSportError
)
from app.utils.caching import (
    cache_response, 
    invalidate_cache,
    CacheKeys,
    CacheStrategy,
    cache_get_or_set
)
from app.utils.monitoring import get_monitoring_service
from app.utils.error_handler import log_error
from datetime import datetime
from typing import List, Optional

router = APIRouter()


# ============================================================================
# EXAMPLE 1: Using Input Validation
# ============================================================================

@router.get("/example/predictions", response_model=List[dict])
async def get_predictions_example(
    filters: PredictionFilterRequest = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Example of using input validation
    
    The PredictionFilterRequest model automatically validates:
    - sport is in valid list
    - confidence is 0-1
    - prediction_type is valid
    - limit is 1-1000
    
    No need for manual validation!
    """
    # Input is pre-validated by Pydantic
    predictions = await db.query(Prediction).filter(
        Prediction.sport == filters.sport,
        Prediction.confidence >= filters.min_confidence,
        Prediction.confidence <= filters.max_confidence
    ).limit(filters.limit).offset(filters.offset).all()
    
    return predictions


# ============================================================================
# EXAMPLE 2: Using Caching Decorator
# ============================================================================

@router.get("/example/cached-predictions/{sport}")
@cache_response(
    ttl=CacheStrategy.cache_predictions(),  # 5 minutes
    prefix="predictions"
)
async def get_cached_predictions_example(
    sport: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Example of using caching decorator
    
    Responses are automatically cached for the specified TTL.
    All subsequent requests within TTL will be served from cache.
    """
    if sport not in ['nba', 'nhl', 'mlb', 'nfl', 'soccer']:
        raise InvalidSportError(sport, ['nba', 'nhl', 'mlb', 'nfl', 'soccer'])
    
    predictions = await db.query(Prediction).filter(
        Prediction.sport == sport
    ).all()
    
    return predictions


# ============================================================================
# EXAMPLE 3: Using Cache Invalidation
# ============================================================================

@router.post("/example/predictions")
@invalidate_cache(pattern=CacheKeys.INVALIDATE_PREDICTIONS)  # Clears all prediction cache
async def create_prediction_example(
    prediction_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Example of using cache invalidation decorator
    
    When this endpoint is called, all cached predictions
    are automatically invalidated so they're refreshed.
    """
    new_prediction = Prediction(**prediction_data)
    db.add(new_prediction)
    await db.commit()
    
    return {"id": new_prediction.id, "message": "Prediction created"}


# ============================================================================
# EXAMPLE 4: Using Standardized Error Responses
# ============================================================================

@router.get("/example/predictions/{prediction_id}")
async def get_prediction_detail_example(
    prediction_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Example of using standardized error responses
    
    Raises APIException subclasses that are automatically
    converted to standardized error responses
    """
    prediction = await db.query(Prediction).filter(
        Prediction.id == prediction_id
    ).first()
    
    if not prediction:
        # Automatically converted to standard error response
        raise PredictionNotFoundError(prediction_id)
    
    return prediction


# ============================================================================
# EXAMPLE 5: Manual Caching with cache_get_or_set
# ============================================================================

@router.get("/example/player-props/{sport}/{player_name}")
async def get_player_props_example(
    sport: str,
    player_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Example of manual cache with cache_get_or_set
    
    If data is in cache, returns it.
    Otherwise, calls the factory function and caches the result.
    """
    cache_key = CacheKeys.PLAYER_PROPS_BY_EVENT(f"{sport}:{player_name}")
    
    # Define factory function to fetch data if not cached
    async def fetch_player_props():
        return await db.query(PlayerProps).filter(
            PlayerProps.sport == sport,
            PlayerProps.player_name == player_name
        ).all()
    
    # Get from cache or fetch
    props = await cache_get_or_set(
        cache_key,
        fetch_player_props,
        ttl=CacheStrategy.cache_player_props()
    )
    
    return props


# ============================================================================
# EXAMPLE 6: Using Monitoring Service
# ============================================================================

@router.post("/example/follow-prediction/{prediction_id}")
async def follow_prediction_example(
    prediction_id: str,
    request: FollowPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Example of using monitoring service
    
    Track key business metrics like follows/purchases
    """
    monitoring = get_monitoring_service()
    
    prediction = await db.query(Prediction).filter(
        Prediction.id == prediction_id
    ).first()
    
    if not prediction:
        raise PredictionNotFoundError(prediction_id)
    
    # Record the prediction for monitoring
    monitoring.models.record_prediction(
        prediction_id=prediction.id,
        confidence=prediction.confidence,
        model_name="ensemble",
        sport=prediction.sport
    )
    
    # Create follow record
    follow = PredictionFollow(
        user_id=current_user.id,
        prediction_id=prediction_id,
        amount=request.amount
    )
    db.add(follow)
    await db.commit()
    
    return {
        "id": follow.id,
        "message": f"Following prediction for ${request.amount:.2f}"
    }


# ============================================================================
# EXAMPLE 7: Using Error Logging
# ============================================================================

@router.get("/example/predictions/resolve/{prediction_id}")
async def resolve_prediction_example(
    prediction_id: str,
    result: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Example of using centralized error logging
    """
    try:
        prediction = await db.query(Prediction).filter(
            Prediction.id == prediction_id
        ).first()
        
        if not prediction:
            raise PredictionNotFoundError(prediction_id)
        
        prediction.resolved_at = datetime.utcnow()
        prediction.result = result
        await db.commit()
        
        return {"message": "Prediction resolved"}
        
    except Exception as e:
        # Centralized error logging
        log_error(
            error_code="PREDICTION_RESOLUTION_FAILED",
            message=f"Failed to resolve prediction {prediction_id}",
            exception=e,
            level="error"
        )
        
        raise


# ============================================================================
# EXAMPLE 8: Combining All Features
# ============================================================================

@router.get("/example/complex/{sport}")
@cache_response(ttl=300, prefix="complex_predictions")
async def complex_predictions_example(
    sport: str,
    filters: PredictionFilterRequest = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Example combining multiple features:
    - Input validation (automatic via Pydantic)
    - Caching (automatic via decorator)
    - Error handling (standardized responses)
    - Monitoring (track requests and errors)
    """
    monitoring = get_monitoring_service()
    
    try:
        # Input is validated by PredictionFilterRequest
        if sport not in ['nba', 'nhl', 'mlb', 'nfl', 'soccer']:
            raise InvalidSportError(sport, ['nba', 'nhl', 'mlb', 'nfl', 'soccer'])
        
        # Fetch predictions with filters
        query = db.query(Prediction).filter(
            Prediction.sport == sport,
            Prediction.confidence >= filters.min_confidence,
            Prediction.confidence <= filters.max_confidence
        )
        
        predictions = await query.limit(filters.limit).offset(filters.offset).all()
        
        # Create paginated response
        total = await query.count()
        
        return {
            "data": predictions,
            "pagination": {
                "limit": filters.limit,
                "offset": filters.offset,
                "total": total,
                "has_more": (filters.offset + filters.limit) < total
            }
        }
        
    except InvalidSportError as e:
        # This is automatically handled by error handler
        log_error(
            error_code=e.error_code,
            message=e.message,
            level="warning"
        )
        raise


# ============================================================================
# USAGE PATTERNS
# ============================================================================

"""
Pattern 1: Simple caching - use decorator
@cache_response(ttl=300, prefix="mydata")
async def my_route():
    return data

Pattern 2: Cache invalidation
@invalidate_cache(pattern="mydata:*")
async def update_route():
    # Update happens, cache is cleared
    pass

Pattern 3: Manual cache with fallback
result = await cache_get_or_set(
    key="mykey",
    factory=lambda: fetch_from_db(),
    ttl=300
)

Pattern 4: Error handling
from app.models.responses import SomeError

@app.get("/route")
async def my_route():
    if error_condition:
        raise SomeError("message")  # Auto-formatted response
    return result

Pattern 5: Monitoring
monitoring = get_monitoring_service()
monitoring.performance.record_request(...)
monitoring.errors.record_error(...)

Pattern 6: Input validation
def my_route(request: MyRequestModel = Depends())
    # request is auto-validated!
    pass
"""
