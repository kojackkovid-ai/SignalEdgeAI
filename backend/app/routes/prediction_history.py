"""
Prediction History API Routes
Endpoints for retrieving user prediction history and accuracy statistics
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth_service import get_current_user
from app.models.db_models import User
from app.services.prediction_history_service import PredictionHistoryService
from typing import Optional

router = APIRouter()

@router.get("/history")
async def get_prediction_history(
    sport: Optional[str] = Query(None, description="Filter by sport"),
    outcome: Optional[str] = Query(None, description="Filter by outcome: hit, miss, pending"),
    confidence_min: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's prediction history with optional filters
    
    Returns:
    - predictions: List of historical predictions
    - total: Total count of matching predictions
    - stats: User's overall accuracy statistics
    """
    service = PredictionHistoryService(db)
    
    predictions, total = await service.get_user_prediction_history(
        user_id=current_user_id,
        sport_key=sport,
        outcome=outcome,
        confidence_min=confidence_min,
        limit=limit,
        offset=offset
    )
    
    stats = await service.get_user_stats(current_user_id)
    
    return {
        'predictions': predictions,
        'total': total,
        'stats': stats,
        'limit': limit,
        'offset': offset
    }

@router.get("/stats")
async def get_user_stats(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall accuracy statistics for user
    
    Returns:
    - total: Total predictions made
    - hits: Correct predictions
    - misses: Incorrect predictions
    - win_rate: Percentage of correct predictions
    - avg_confidence: Average confidence of predictions
    - roi: Return on investment (if stored)
    """
    service = PredictionHistoryService(db)
    stats = await service.get_user_stats(current_user_id)
    return stats

@router.get("/stats/by-sport")
async def get_stats_by_sport(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get accuracy statistics broken down by sport
    
    Returns dictionary:
    {
        'nba': {'total': 150, 'hits': 85, 'win_rate': 0.567, ...},
        'nfl': {'total': 80, 'hits': 42, 'win_rate': 0.525, ...},
        ...
    }
    """
    service = PredictionHistoryService(db)
    sport_stats = await service.get_user_stats_by_sport(current_user_id)
    return sport_stats

@router.get("/stats/recent-trends")
async def get_recent_trends(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, ge=1, le=365)
):
    """
    Get accuracy trends over recent period
    
    Returns rolling accuracy by date:
    [
        {'date': '2026-03-07', 'accuracy': 0.55, 'predictions_count': 15},
        {'date': '2026-03-06', 'accuracy': 0.62, 'predictions_count': 21},
        ...
    ]
    """
    from sqlalchemy import select, func, Integer
    from app.models.prediction_records import PredictionRecord
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(
            func.date(PredictionRecord.created_at).label('date'),
            func.count().label('count'),
            func.sum(
                func.cast(
                    PredictionRecord.outcome == 'hit',
                    Integer()
                )
            ).label('hits')
        ).where(
            PredictionRecord.user_id == current_user_id,
            PredictionRecord.created_at > cutoff_date,
            PredictionRecord.outcome.in_(['hit', 'miss'])
        ).group_by(func.date(PredictionRecord.created_at))
        .order_by(func.date(PredictionRecord.created_at))
    )
    
    trends = []
    for row in result:
        accuracy = (row.hits / row.count) if row.count > 0 else 0.0
        trends.append({
            'date': str(row.date),
            'accuracy': accuracy,
            'predictions_count': row.count
        })
    
    return trends

@router.get("/confidence-calibration")
async def get_confidence_calibration(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get confidence calibration analysis
    Shows if user's confidence scores match actual outcomes
    
    Returns:
    {
        '50-60%': {'predicted': 0.55, 'actual': 0.58, 'calibrated': true},
        '60-70%': {'predicted': 0.65, 'actual': 0.72, 'calibrated': true},
        ...
    }
    """
    from sqlalchemy import select, func, and_
    from app.models.prediction_records import PredictionRecord
    
    # Get all user predictions with outcomes
    result = await db.execute(
        select(PredictionRecord).where(
            and_(
                PredictionRecord.user_id == current_user_id,
                PredictionRecord.outcome.in_(['hit', 'miss'])
            )
        )
    )
    
    predictions = result.scalars().all()
    
    # Group into confidence buckets
    buckets = {
        '50-60%': (0.50, 0.60),
        '60-70%': (0.60, 0.70),
        '70-80%': (0.70, 0.80),
        '80-90%': (0.80, 0.90),
        '90-100%': (0.90, 1.00)
    }
    
    calibration = {}
    for bucket_name, (min_conf, max_conf) in buckets.items():
        bucket_preds = [
            p for p in predictions
            if min_conf <= p.confidence < max_conf
        ]
        
        if len(bucket_preds) == 0:
            continue
        
        actual_accuracy = sum(1 for p in bucket_preds if p.outcome == 'hit') / len(bucket_preds)
        predicted_accuracy = (min_conf + max_conf) / 2
        calibration_error = abs(actual_accuracy - predicted_accuracy)
        
        calibration[bucket_name] = {
            'count': len(bucket_preds),
            'predicted_accuracy': predicted_accuracy,
            'actual_accuracy': actual_accuracy,
            'calibration_error': calibration_error,
            'calibrated': calibration_error < 0.05
        }
    
    return {
        'calibration_by_bucket': calibration,
        'recommendation': 'Your confidence scores are well-calibrated' if all(
            v.get('calibrated') for v in calibration.values()
        ) else 'Consider scaling your confidence scores'
    }

@router.get("/compare-models")
async def compare_model_performance(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Compare performance of individual models
    
    Returns:
    {
        'models': {
            'lightgbm': {'accuracy': 0.58, 'predictions': 45},
            'neural_network': {'accuracy': 0.55, 'predictions': 45},
            'ensemble': {'accuracy': 0.62, 'predictions': 45}
        }
    }
    """
    from sqlalchemy import select
    from app.models.prediction_records import PredictionRecord
    
    result = await db.execute(
        select(PredictionRecord).where(
            PredictionRecord.user_id == current_user_id,
            PredictionRecord.outcome.in_(['hit', 'miss'])
        )
    )
    
    predictions = result.scalars().all()
    
    # Extract model weights and compare
    model_performance = {}
    
    for pred in predictions:
        if pred.model_weights:
            for model_name, model_info in pred.model_weights.items():
                if model_name not in model_performance:
                    model_performance[model_name] = {'hits': 0, 'total': 0}
                
                model_performance[model_name]['total'] += 1
                if pred.outcome == 'hit':
                    model_performance[model_name]['hits'] += 1
    
    # Calculate accuracy for each model
    for model_name, stats in model_performance.items():
        stats['accuracy'] = (
            stats['hits'] / stats['total']
            if stats['total'] > 0 else 0.0
        )
    
    return {'models': model_performance}
