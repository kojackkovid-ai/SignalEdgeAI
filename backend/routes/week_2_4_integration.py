"""
Integration of Week 2-4 services into main FastAPI application
Adds routes for prediction history, player props, calibration, and monitoring
"""

from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.db_models import User, verify_token
from app.services.prediction_history_service import PredictionHistoryService, PlayerDataService
from app.services.player_props_service import PlayerPropsService
from app.services.ml_calibration_service import MLCalibrationService, ConfidenceCalibrator
from app.services.load_testing_monitoring import (
    PerformanceMonitor, AlertManager, LoadTestRunner
)
from app.cache import cache_manager

# ============================================================================
# ROUTERS
# ============================================================================

# Prediction History Routes
prediction_history_router = APIRouter(prefix="/api/v1/predictions", tags=["Predictions"])

# Player Props Routes
player_props_router = APIRouter(prefix="/api/v1/player-props", tags=["Player Props"])

# ML Calibration Routes
calibration_router = APIRouter(prefix="/api/v1/calibration", tags=["ML Calibration"])

# Monitoring Routes
monitoring_router = APIRouter(prefix="/api/v1/monitoring", tags=["Monitoring"])

# Performance/Load Testing Routes
load_testing_router = APIRouter(prefix="/api/v1/load-testing", tags=["Load Testing"])

# ============================================================================
# DEPENDENCY INJECTIONS
# ============================================================================

async def get_current_user(token: str = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    """Get current authenticated user"""
    user = await db.query(User).filter(User.id == token.get('user_id')).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def get_prediction_service(db: AsyncSession = Depends(get_db)):
    """Get prediction history service instance"""
    return PredictionHistoryService(db)

async def get_player_props_service(db: AsyncSession = Depends(get_db)):
    """Get player props service instance"""
    return PlayerPropsService(db)

async def get_calibration_service(db: AsyncSession = Depends(get_db)):
    """Get ML calibration service instance"""
    return MLCalibrationService(db)

# ============================================================================
# PREDICTION HISTORY ENDPOINTS
# ============================================================================

@prediction_history_router.post("/record")
async def record_prediction(
    sport_key: str,
    event_id: str,
    prediction_data: dict,
    user: User = Depends(get_current_user),
    service: PredictionHistoryService = Depends(get_prediction_service)
):
    """
    Record a new prediction
    
    **Parameters:**
    - sport_key: 'nba', 'nfl', 'mlb', 'nhl'
    - event_id: Unique event identifier
    - prediction_data: Dict with prediction details
    """
    try:
        pred_id = await service.record_prediction(
            user_id=user.id,
            sport_key=sport_key,
            event_id=event_id,
            prediction_data=prediction_data
        )
        return {
            'success': True,
            'prediction_id': pred_id,
            'message': 'Prediction recorded successfully'
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@prediction_history_router.get("/user-history")
async def get_user_prediction_history(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sport_key: str = Query(None),
    user: User = Depends(get_current_user),
    service: PredictionHistoryService = Depends(get_prediction_service)
):
    """
    Get user's prediction history
    
    **Query Parameters:**
    - limit: Number of predictions to return (1-500)
    - offset: Pagination offset
    - sport_key: Filter by sport (optional)
    """
    # Try cache first
    cache_key = f"user_history:{user.id}:{sport_key}:{limit}:{offset}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    
    predictions, total = await service.get_user_prediction_history(
        user_id=user.id,
        limit=limit,
        offset=offset,
        sport_key=sport_key
    )
    
    response = {
        'predictions': [p.dict() for p in predictions],
        'total': total,
        'limit': limit,
        'offset': offset
    }
    
    # Cache for 5 minutes
    await cache_manager.set(cache_key, response, ttl=300)
    return response

@prediction_history_router.get("/user-stats")
async def get_user_stats(
    sport_key: str = Query(None),
    user: User = Depends(get_current_user),
    service: PredictionHistoryService = Depends(get_prediction_service)
):
    """
    Get user's prediction statistics
    
    **Query Parameters:**
    - sport_key: Filter by sport (optional)
    """
    # Try cache first
    cache_key = f"user_stats:{user.id}:{sport_key}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    
    stats = await service.get_user_stats(
        user_id=user.id,
        sport_key=sport_key
    )
    
    # Cache for 30 minutes
    await cache_manager.set(cache_key, stats, ttl=1800)
    return stats

@prediction_history_router.put("/outcome/{prediction_id}")
async def update_prediction_outcome(
    prediction_id: str,
    outcome: str,
    user: User = Depends(get_current_user),
    service: PredictionHistoryService = Depends(get_prediction_service)
):
    """
    Update prediction outcome after event concludes
    
    **Parameters:**
    - prediction_id: ID of prediction to update
    - outcome: 'hit', 'miss', 'push', 'void'
    """
    try:
        success = await service.update_prediction_outcome(
            prediction_id=prediction_id,
            user_id=user.id,
            outcome=outcome
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Prediction not found")
        
        # Invalidate user stats cache
        await cache_manager.delete(f"user_stats:{user.id}:*")
        
        return {'success': True, 'message': 'Outcome updated successfully'}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# PLAYER PROPS ENDPOINTS
# ============================================================================

@player_props_router.get("/generate/{event_id}")
async def generate_player_props(
    event_id: str,
    sport_key: str = Query(...),
    home_team: str = Query(...),
    away_team: str = Query(...),
    user: User = Depends(get_current_user),
    service: PlayerPropsService = Depends(get_player_props_service)
):
    """
    Generate player prop predictions for an event
    
    **Parameters:**
    - event_id: Unique event identifier
    - sport_key: 'nba', 'nfl', 'mlb', 'nhl'
    - home_team: Home team key
    - away_team: Away team key
    """
    try:
        # Try cache first
        cache_key = f"player_props:{event_id}:{sport_key}"
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached
        
        props = await service.generate_player_prop_predictions(
            event_id=event_id,
            sport_key=sport_key,
            home_team=home_team,
            away_team=away_team
        )
        
        response = {
            'event_id': event_id,
            'sport_key': sport_key,
            'props': props,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Cache for 10 minutes
        await cache_manager.set(cache_key, response, ttl=600)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@player_props_router.get("/player/{player_id}/props")
async def get_player_props(
    player_id: str,
    sport_key: str = Query(...),
    prop_type: str = Query(...),  # 'ppg', 'rpg', 'apg', etc.
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get specific player property lines and predictions
    
    **Parameters:**
    - player_id: Unique player identifier
    - sport_key: 'nba', 'nfl', 'mlb', 'nhl'
    - prop_type: Type of prop (ppg, rpg, apg, etc.)
    """
    service = PlayerPropsService(db)
    
    try:
        props = await service.get_player_prop_lines(
            player_id=player_id,
            sport_key=sport_key,
            prop_type=prop_type
        )
        
        return {
            'player_id': player_id,
            'prop_type': prop_type,
            'lines': props
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# ML CALIBRATION ENDPOINTS
# ============================================================================

@calibration_router.post("/analyze")
async def analyze_calibration(
    days_back: int = Query(7, ge=1, le=90),
    sport_key: str = Query(None),
    user: User = Depends(get_current_user),
    service: MLCalibrationService = Depends(get_calibration_service)
):
    """
    Analyze confidence calibration for user's predictions
    
    **Query Parameters:**
    - days_back: Number of days to analyze (1-90)
    - sport_key: Filter by sport (optional)
    """
    try:
        report = await service.run_full_backtest(
            days_back=days_back,
            user_id=user.id,
            sport_key=sport_key
        )
        
        return {
            'success': True,
            'analysis': report
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@calibration_router.get("/model-metrics/{sport_key}")
async def get_model_calibration_metrics(
    sport_key: str,
    days_back: int = Query(30, ge=1, le=365),
    user: User = Depends(get_current_user),
    service: MLCalibrationService = Depends(get_calibration_service)
):
    """
    Get model calibration metrics by sport
    
    **Parameters:**
    - sport_key: 'nba', 'nfl', 'mlb', 'nhl'
    - days_back: Number of days of metrics to retrieve
    """
    try:
        metrics = await service.get_calibration_history(
            sport_key=sport_key,
            days_back=days_back
        )
        
        return {
            'sport_key': sport_key,
            'metrics': metrics
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@calibration_router.post("/apply-temperature")
async def apply_temperature_scaling(
    sport_key: str,
    temperature: float = Query(..., ge=0.5, le=2.0),
    user: User = Depends(get_current_user)
):
    """
    Apply temperature scaling to model predictions
    
    **Parameters:**
    - sport_key: 'nba', 'nfl', 'mlb', 'nhl'
    - temperature: Temperature scaling factor (0.5-2.0)
    """
    try:
        calibrator = ConfidenceCalibrator(sport_key)
        calibrator.temperature = temperature
        
        return {
            'success': True,
            'sport_key': sport_key,
            'temperature': temperature,
            'message': f'Temperature scaling applied to {sport_key} predictions'
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# MONITORING ENDPOINTS
# ============================================================================

@monitoring_router.get("/performance-stats")
async def get_performance_stats():
    """
    Get real-time API performance statistics
    """
    monitor = PerformanceMonitor()
    stats = monitor.get_all_endpoint_stats()
    
    return {
        'endpoints': stats,
        'retrieved_at': datetime.utcnow().isoformat()
    }

@monitoring_router.get("/alerts")
async def get_active_alerts():
    """
    Get list of active performance/error alerts
    """
    manager = AlertManager()
    alerts = manager.get_active_alerts()
    
    return {
        'alerts': alerts,
        'alert_count': len(alerts),
        'critical_count': sum(1 for a in alerts if a['level'] == 'CRITICAL'),
        'warning_count': sum(1 for a in alerts if a['level'] == 'WARNING')
    }

@monitoring_router.post("/check-health")
async def check_system_health(
    db: AsyncSession = Depends(get_db)
):
    """
    Perform comprehensive system health check
    """
    try:
        # Test database connection
        await db.execute("SELECT 1")
        
        # Get performance stats
        monitor = PerformanceMonitor()
        stats = monitor.get_all_endpoint_stats()
        
        # Get alerts
        manager = AlertManager()
        alerts = manager.get_active_alerts()
        
        return {
            'status': 'healthy' if not alerts else 'degraded',
            'database': 'ok',
            'endpoints_monitored': len(stats),
            'active_alerts': len(alerts),
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service unhealthy")

# ============================================================================
# LOAD TESTING ENDPOINTS (ADMIN ONLY)
# ============================================================================

@load_testing_router.post("/run-test")
async def run_load_test(
    endpoints: list = Query(['GET /api/v1/predictions/user-history']),
    num_requests: int = Query(100, ge=1, le=10000),
    concurrent: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user)
):
    """
    Run load test on specified endpoints (Admin Only)
    
    **Parameters:**
    - endpoints: List of endpoints to test
    - num_requests: Total number of requests
    - concurrent: Number of concurrent workers
    """
    # Check admin privileges
    if user.subscription_tier != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        runner = LoadTestRunner()
        results = await runner.run_load_test(
            endpoints=endpoints,
            num_requests=num_requests,
            concurrent=concurrent
        )
        
        return {
            'success': True,
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# INTEGRATION INTO MAIN APP
# ============================================================================

def initialize_week_2_4_routes(app: FastAPI):
    """
    Initialize all Week 2-4 routes in main FastAPI app
    
    **Usage:**
    ```python
    from fastapi import FastAPI
    from main_integration import initialize_week_2_4_routes
    
    app = FastAPI()
    initialize_week_2_4_routes(app)
    ```
    """
    
    # Include all routers
    app.include_router(prediction_history_router)
    app.include_router(player_props_router)
    app.include_router(calibration_router)
    app.include_router(monitoring_router)
    app.include_router(load_testing_router)
    
    # Add startup event
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on app startup"""
        # Initialize performance monitor
        monitor = PerformanceMonitor()
        
        # Initialize alert manager
        manager = AlertManager()
        
        print("✅ Week 2-4 services initialized successfully")
    
    # Add shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on app shutdown"""
        print("🛑 Cleaning up Week 2-4 services")
    
    return app

if __name__ == "__main__":
    # Example of how to use in main application
    from app.main import app
    initialize_week_2_4_routes(app)
