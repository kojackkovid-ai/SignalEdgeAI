"""
ML Models and Training API Routes
Endpoints for checking model training status, performance metrics, and triggering retraining
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pydantic import BaseModel

from app.database import AsyncSessionLocal, get_db
from app.models.db_models import (
    TrainingSession,
    ModelPerformanceMetrics,
    ScheduledTrainingJob,
    User,
)
from app.services.training_scheduler import get_training_scheduler
from app.services.model_performance_monitor import get_model_monitor
from app.services.ml_training_dashboard import get_dashboard
from app.services.auth_service import get_current_user

logger = logging.getLogger(__name__)

# Pydantic Schemas
class TrainingStatusResponse(BaseModel):
    scheduler_running: bool
    scheduled_jobs: List[Dict]
    next_runs: Dict[str, str]
    recent_history: List[Dict]

class TrainingSessionResponse(BaseModel):
    id: int
    sport_key: str
    market_type: str
    started_at: str
    completed_at: Optional[str]
    duration_seconds: Optional[float]
    training_samples: Optional[int]
    validation_accuracy: Optional[float]
    status: str
    trigger_reason: Optional[str]

class ModelPerformanceResponse(BaseModel):
    sport_key: str
    market_type: str
    accuracy: float
    total_predictions: int
    correct_predictions: int
    last_updated: str

class TriggerTrainingRequest(BaseModel):
    sport_key: str
    market_type: str
    reason: Optional[str] = "manual"

class TriggerTrainingResponse(BaseModel):
    message: str
    job_id: Optional[int] = None

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Restrict endpoint to admin-tier users only."""
    if not getattr(current_user, "subscription_tier", None) == "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/api/ml/training/status", response_model=TrainingStatusResponse, tags=["ML Training"])
async def get_training_status(
    session: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Get overall training scheduler status and scheduled jobs
    
    Returns:
        - Scheduler running status
        - List of all scheduled training jobs
        - Next scheduled run times
        - Recent training history
    """
    try:
        scheduler = await get_training_scheduler()
        status = await scheduler.get_scheduler_status(session)
        return status
    except Exception as e:
        logger.error(f"Error getting training status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/ml/training/history", response_model=List[TrainingSessionResponse], tags=["ML Training"])
async def get_training_history(
    sport_key: Optional[str] = Query(None, description="Filter by sport"),
    market_type: Optional[str] = Query(None, description="Filter by market type"),
    limit: int = Query(50, ge=1, le=500, description="Max results"),
    session: AsyncSession = Depends(get_db)
) -> List[Dict]:
    """
    Get training session history
    
    Returns:
        - List of past training sessions
        - Status, duration, accuracy metrics
        - Trigger reasons
    """
    try:
        if session is None:
            session = AsyncSessionLocal()
        
        query = select(TrainingSession).order_by(TrainingSession.completed_at.desc())
        
        if sport_key:
            query = query.where(TrainingSession.sport_key == sport_key)
        if market_type:
            query = query.where(TrainingSession.market_type == market_type)
        
        result = await session.execute(query.limit(limit))
        sessions = result.scalars().all()
        
        return [
            {
                'id': s.id,
                'sport_key': s.sport_key,
                'market_type': s.market_type,
                'started_at': s.started_at.isoformat(),
                'completed_at': s.completed_at.isoformat() if s.completed_at else None,
                'duration_seconds': s.duration_seconds,
                'training_samples': s.training_samples,
                'validation_accuracy': s.validation_accuracy,
                'status': s.status,
                'trigger_reason': s.trigger_reason,
                'error': s.error_message
            }
            for s in sessions
        ]
    except Exception as e:
        logger.error(f"Error getting training history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/ml/models/{sport_key}/{market_type}/health", tags=["Model Health"])
async def get_model_health(
    sport_key: str,
    market_type: str,
    days: int = Query(7, ge=1, le=90),
    session: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Get health report for a specific model
    
    Includes:
    - Current accuracy and performance metrics
    - Confidence levels
    - Time since last training
    - Drift warnings
    - Recommendations
    """
    try:
        if session is None:
            session = AsyncSessionLocal()
        
        monitor = await get_model_monitor()
        health = await monitor.get_model_health(session, sport_key, market_type, days)
        return health
    except Exception as e:
        logger.error(f"Error getting model health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/ml/models/{sport_key}/{market_type}/performance", tags=["Model Performance"])
async def get_model_performance_metrics(
    sport_key: str,
    market_type: str,
    days: int = Query(7, ge=1, le=90),
    session: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Get detailed performance metrics for a model over time
    
    Returns:
    - Accuracy trend over time
    - Hit/miss counts
    - Confidence metrics
    - Drift detection results
    """
    try:
        if session is None:
            session = AsyncSessionLocal()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = await session.execute(
            select(ModelPerformanceMetrics).where(
                (ModelPerformanceMetrics.sport_key == sport_key) &
                (ModelPerformanceMetrics.market_type == market_type) &
                (ModelPerformanceMetrics.measurement_date >= cutoff_date)
            ).order_by(ModelPerformanceMetrics.measurement_date)
        )
        metrics = result.scalars().all()
        
        if not metrics:
            return {
                'sport_key': sport_key,
                'market_type': market_type,
                'message': 'No performance data available',
                'metrics': []
            }
        
        # Calculate drift
        monitor = await get_model_monitor()
        drift_detection = await monitor.detect_drift(session, sport_key, market_type, days)
        
        return {
            'sport_key': sport_key,
            'market_type': market_type,
            'period_days': days,
            'metrics': [
                {
                    'date': m.measurement_date.isoformat(),
                    'window_start': m.window_start.isoformat(),
                    'window_end': m.window_end.isoformat(),
                    'predictions_count': m.predictions_count,
                    'hit_count': m.hit_count,
                    'miss_count': m.miss_count,
                    'accuracy': m.accuracy,
                    'confidence_mean': m.confidence_mean,
                    'confidence_std': m.confidence_std,
                    'roi': m.roi,
                    'has_drift': m.has_drift,
                    'drift_severity': m.drift_severity
                }
                for m in metrics
            ],
            'drift_detection': drift_detection
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/ml/training/trigger", tags=["ML Training"])
async def trigger_manual_training(
    sport_key: Optional[str] = Query(None, description="Optional: specific sport to retrain"),
    market_type: Optional[str] = Query(None, description="Optional: specific market to retrain"),
    session: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Manually trigger model retraining
    
    Can retrain:
    - All models (if sport_key and market_type omitted)
    - Specific sport (if only sport_key provided)
    - Specific sport/market combination (if both provided)
    """
    try:
        if session is None:
            session = AsyncSessionLocal()
        
        scheduler = await get_training_scheduler()
        
        if sport_key and market_type:
            # Find job for this specific model
            result = await session.execute(
                select(ScheduledTrainingJob).where(
                    (ScheduledTrainingJob.sport_key == sport_key) &
                    (ScheduledTrainingJob.market_type == market_type)
                )
            )
            job = result.scalars().first()
            
            if not job:
                raise HTTPException(
                    status_code=404,
                    detail=f"No training job found for {sport_key}/{market_type}"
                )
            
            from app.services.training_scheduler import TrainingTriggerReason
            training_session = await scheduler._execute_training_job(
                session,
                job,
                TrainingTriggerReason.MANUAL
            )
            
            return {
                'status': 'triggered',
                'training_session_id': training_session.id,
                'sport_key': sport_key,
                'market_type': market_type,
                'trigger': 'manual'
            }
        else:
            # Trigger all models
            result = await session.execute(select(ScheduledTrainingJob))
            jobs = result.scalars().all()
            
            trained_count = 0
            from app.services.training_scheduler import TrainingTriggerReason
            
            for job in jobs:
                if sport_key and job.sport_key != sport_key:
                    continue
                
                await scheduler._execute_training_job(
                    session,
                    job,
                    TrainingTriggerReason.MANUAL
                )
                trained_count += 1
            
            return {
                'status': 'triggered',
                'total_models_triggered': trained_count,
                'sport_filter': sport_key,
                'trigger': 'manual'
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/ml/models/all/health", tags=["Model Health"])
async def get_all_models_health(
    days: int = Query(7, ge=1, le=90),
    session: AsyncSession = Depends(get_db)
) -> List[Dict]:
    """
    Get health status for all trained models
    
    Quick overview of:
    - Which models are healthy
    - Which models need retraining
    - Models with drift warnings
    """
    try:
        if session is None:
            session = AsyncSessionLocal()
        
        # Get all active models from schedule
        result = await session.execute(
            select(ScheduledTrainingJob).where(ScheduledTrainingJob.is_enabled == True)
        )
        jobs = result.scalars().all()
        
        monitor = await get_model_monitor()
        health_reports = []
        
        for job in jobs:
            try:
                health = await monitor.get_model_health(
                    session,
                    job.sport_key,
                    job.market_type,
                    days
                )
                health_reports.append(health)
            except Exception as e:
                logger.debug(f"Error getting health for {job.sport_key}/{job.market_type}: {e}")
                health_reports.append({
                    'status': 'error',
                    'sport_key': job.sport_key,
                    'market_type': job.market_type,
                    'message': str(e)
                })
        
        # Sort by health status (critical first)
        status_order = {'critical': 0, 'poor': 1, 'fair': 2, 'good': 3, 'no_data': 4, 'error': 5}
        health_reports.sort(
            key=lambda x: status_order.get(x.get('status'), 10)
        )
        
        return health_reports
    
    except Exception as e:
        logger.error(f"Error getting all models health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/ml/training/jobs/{job_name}/enable", tags=["ML Training"])
async def enable_training_job(
    job_name: str,
    session: AsyncSession = Depends(get_db)
) -> Dict:
    """Enable a training job"""
    try:
        if session is None:
            session = AsyncSessionLocal()
        
        result = await session.execute(
            select(ScheduledTrainingJob).where(ScheduledTrainingJob.job_name == job_name)
        )
        job = result.scalars().first()
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_name} not found")
        
        job.is_enabled = True
        await session.commit()
        
        return {'status': 'enabled', 'job_name': job_name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/ml/training/jobs/{job_name}/disable", tags=["ML Training"])
async def disable_training_job(
    job_name: str,
    session: AsyncSession = Depends(get_db)
) -> Dict:
    """Disable a training job"""
    try:
        if session is None:
            session = AsyncSessionLocal()
        
        result = await session.execute(
            select(ScheduledTrainingJob).where(ScheduledTrainingJob.job_name == job_name)
        )
        job = result.scalars().first()
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_name} not found")
        
        job.is_enabled = False
        await session.commit()
        
        return {'status': 'disabled', 'job_name': job_name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/ml/dashboard", tags=["ML Training Dashboard"])
async def get_training_dashboard(
    session: AsyncSession = Depends(lambda: AsyncSessionLocal())
) -> Dict:
    """
    ✨ Comprehensive ML Training Pipeline Dashboard
    
    Returns complete overview of:
    - Scheduler operational status
    - Recent training sessions (last 7 days)
    - Model health metrics across all sports
    - Active performance drift alerts
    - Platform-wide prediction metrics
    - Scheduled training jobs (next 5 runs)
    
    This dashboard provides all information needed to monitor model training,
    detect performance issues, and ensure models stay up-to-date.
    """
    try:
        dashboard = await get_dashboard()
        summary = await dashboard.get_dashboard_summary(session)
        return summary
    except Exception as e:
        logger.error(f"Error getting training dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/ml/models/{sport_key}/{market_type}/trend", tags=["Model Performance"])
async def get_model_performance_trend(
    sport_key: str,
    market_type: str,
    days: int = Query(30, ge=7, le=180, description="Number of days to analyze"),
    session: AsyncSession = Depends(lambda: AsyncSessionLocal())
) -> Dict:
    """
    📈 Get performance trend for a specific model
    
    Shows how accuracy and metrics change over time with:
    - Accuracy graphs
    - Hit/miss ratios
    - Confidence trends
    - Drift detection results
    
    Useful for identifying performance degradation patterns
    """
    try:
        dashboard = await get_dashboard()
        trend = await dashboard.get_model_performance_trend(session, sport_key, market_type, days)
        return trend
    except Exception as e:
        logger.error(f"Error getting performance trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))
