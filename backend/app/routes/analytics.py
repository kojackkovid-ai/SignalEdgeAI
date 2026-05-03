"""
Analytics API Routes
Admin/Dashboard endpoints for viewing analytics and prediction accuracy
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from app.database import get_db
from app.services.auth_service import get_current_user
from app.services.analytics_service import AnalyticsService
from app.models.db_models import User, Prediction
from datetime import datetime, timedelta
import numpy as np
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Restrict endpoint to admin-tier users only."""
    if getattr(current_user, "subscription_tier", None) != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


class EventTrackingRequest(BaseModel):
    """Request body for event tracking"""
    event_type: str
    event_data: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    user_agent: Optional[str] = None
    request_duration_ms: Optional[float] = None


async def get_analytics_service() -> AnalyticsService:
    """Get analytics service"""
    return AnalyticsService()


@router.post("/event")
async def track_event(
    request: EventTrackingRequest,
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Track a user event from frontend.
    This endpoint is called by the frontend to log user actions.
    """
    await service.log_event(
        db=db,
        user_id=request.user_id,
        event_type=request.event_type,
        event_data=request.event_data,
        session_id=request.session_id,
        user_agent=request.user_agent,
        request_duration_ms=request.request_duration_ms,
    )
    return {'status': 'tracked'}


@router.get("/conversion-funnel")
async def get_conversion_funnel(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get overall conversion funnel metrics.
    Shows how many users move through each stage of the funnel.
    """
    result = await service.get_conversion_funnel(db)
    return result


@router.get("/daily-active-users")
async def get_daily_active_users(
    days: int = Query(30, ge=1, le=365),
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get daily active user count for the past N days.
    """
    result = await service.get_daily_active_users(db, days)
    return {
        'period_days': days,
        'daily_active_users': result,
    }


@router.get("/events")
async def get_event_analytics(
    days: int = Query(30, ge=1, le=365),
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get event analytics showing distribution of user actions.
    """
    result = await service.get_event_analytics(db, days)
    return result


@router.get("/churn")
async def get_churn_analysis(
    days: int = Query(90, ge=1, le=365),
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get user churn metrics showing retention and churned users.
    """
    result = await service.get_churn_analysis(db, days)
    return result


@router.get("/revenue")
async def get_revenue_metrics(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get revenue metrics including MRR, ARPU, and tier breakdown.
    """
    result = await service.get_revenue_metrics(db)
    return result


@router.get("/dashboard")
async def get_analytics_dashboard(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get comprehensive analytics dashboard with all key metrics.
    """
    try:
        funnel = await service.get_conversion_funnel(db)
        dau = await service.get_daily_active_users(db, 30)
        events = await service.get_event_analytics(db, 30)
        churn = await service.get_churn_analysis(db, 90)
        revenue = await service.get_revenue_metrics(db)

        return {
            'conversion_funnel': funnel,
            'daily_active_users': dau,
            'events': events,
            'churn': churn,
            'revenue': revenue,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            'error': str(e),
            'message': 'Failed to generate analytics dashboard',
        }


# ============================================================================
# PREDICTION ACCURACY ANALYTICS - Phase 4
# ============================================================================

def calculate_win_rate(predictions) -> float:
    """Calculate win rate from predictions."""
    if not predictions:
        return 0.0
    wins = sum(1 for p in predictions if p.result == "win")
    return wins / len(predictions)


def calculate_roi(predictions) -> float:
    """Calculate ROI from predictions (assumes $100 bet per prediction)."""
    if not predictions:
        return 0.0
    total_profit = 0.0
    for p in predictions:
        if p.result == "win":
            total_profit += 100.0  # Full $100 return on win
        elif p.result == "loss":
            total_profit -= 100.0  # Full $100 loss on loss
        # push/tie: no change
    total_bets = len(predictions) * 100.0
    return total_profit / total_bets if total_bets > 0 else 0.0


def calculate_calibration_error(predictions) -> float:
    """Calculate calibration error."""
    if not predictions:
        return 0.0
    
    bins = {}
    for p in predictions:
        if p.confidence is None:
            continue
        bin_key = round(p.confidence / 5) * 5
        if bin_key not in bins:
            bins[bin_key] = {'count': 0, 'wins': 0}
        bins[bin_key]['count'] += 1
        if p.result == "win":
            bins[bin_key]['wins'] += 1
    
    errors = []
    for bin_key, data in bins.items():
        if data['count'] >= 5:
            expected = bin_key / 100.0
            actual = data['wins'] / data['count']
            errors.append(abs(expected - actual))
    
    return np.mean(errors) if errors else 0.0


@router.get("/debug/prediction-count")
async def debug_prediction_count(db: AsyncSession = Depends(get_db)):
    """Simple debug endpoint to check prediction count"""
    try:
        stmt = select(Prediction)
        result = await db.execute(stmt)
        all_preds = result.scalars().all()
        
        resolved_count = len([p for p in all_preds if p.resolved_at])
        
        return {
            "total": len(all_preds),
            "resolved": resolved_count,
            "status": "ok"
        }
    except Exception as e:
        return {
            "error": str(e),
            "total": 0,
            "resolved": 0,
            "status": "error"
        }

@router.get("/accuracy")
async def get_accuracy_metrics(
    days: int = Query(30, ge=1, le=365),
    sport_key: Optional[str] = None,
    market_type: Optional[str] = None,
    debug: bool = Query(False),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get prediction accuracy metrics.
    
    Returns overall stats, by-sport breakdown, and confidence calibration.
    """
    debug_info = {}
    
    try:
        # Debug: Get database file info
        import os
        from app.config import settings
        db_url = settings.database_url
        debug_info['database_url'] = db_url if 'sqlite' not in db_url else db_url.replace('sqlite+aiosqlite:///', '')
        
        # Check if file exists
        if 'sqlite' in db_url:
            db_path = db_url.replace('sqlite+aiosqlite:///', '')
            if os.path.exists(db_path):
                debug_info['db_file_size'] = os.path.getsize(db_path)
                debug_info['db_file_exists'] = True
            else:
                debug_info['db_file_exists'] = False
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        logger.info(f"[ANALYTICS] Fetching accuracy metrics for last {days} days (cutoff: {cutoff_date})")
        
        # DEBUG: Check how many predictions exist - try with text query
        from sqlalchemy import text
        try:
            raw_result = await db.execute(text("SELECT COUNT(*) as count FROM predictions"))
            raw_count = raw_result.fetchone()[0]
            debug_info['raw_sql_count'] = raw_count
            logger.info(f"[ANALYTICS DEBUG] Raw SQL COUNT result: {raw_count}")
        except Exception as sql_e:
            debug_info['raw_sql_error'] = str(sql_e)
            logger.error(f"[ANALYTICS DEBUG] Raw SQL COUNT failed: {sql_e}")
        
        # DEBUG: Check ORM query
        all_preds_query = select(Prediction)
        all_result = await db.execute(all_preds_query)
        all_predictions = all_result.scalars().all()
        debug_info['orm_count'] = len(all_predictions)
        logger.info(f"[ANALYTICS DEBUG] ORM select(Prediction) result: {len(all_predictions)} predictions")
        
        # Build query (excluding Club 100 access picks)
        query = select(Prediction).filter(
            Prediction.created_at >= cutoff_date,
            Prediction.resolved_at.isnot(None),
            Prediction.sport != 'club_100_access'  # EXCLUDE 5-pick access fee
        )
        
        if sport_key:
            query = query.filter(Prediction.sport_key == sport_key)
        if market_type:
            query = query.filter(Prediction.market_type == market_type)
        
        result = await db.execute(query)
        predictions = result.scalars().all()
        logger.info(f"[ANALYTICS] Found {len(predictions)} resolved predictions matching filters")
        debug_info['filtered_count'] = len(predictions)
        
        if not predictions:
            logger.info("[ANALYTICS] No predictions found, returning zero metrics")
            response = {
                "total_predictions": 0,
                "resolved_predictions": 0,
                "win_rate": 0.0,
                "roi": 0.0,
                "calibration_error": 0.0,
                "by_sport": {},
                "confidence_bins": {},
                "generated_at": datetime.utcnow().isoformat()
            }
            if debug:
                response["_debug"] = debug_info
            return response
        
        # Overall metrics
        win_rate = calculate_win_rate(predictions)
        roi = calculate_roi(predictions)
        calibration_error = calculate_calibration_error(predictions)
        
        # By sport breakdown
        by_sport = {}
        for sport in set(p.sport_key for p in predictions if p.sport_key):
            sport_preds = [p for p in predictions if p.sport_key == sport]
            by_sport[sport] = {
                "accuracy": round(calculate_win_rate(sport_preds), 4),
                "count": len(sport_preds),
                "roi": round(calculate_roi(sport_preds), 4)
            }
        
        # Confidence bins (5% increments)
        confidence_bins = {}
        for conf_target in range(50, 101, 5):
            conf_preds = [
                p for p in predictions
                if p.confidence and conf_target <= p.confidence < conf_target + 5
            ]
            if conf_preds:
                confidence_bins[f"{conf_target}-{conf_target+5}%"] = {
                    "accuracy": round(calculate_win_rate(conf_preds), 4),
                    "count": len(conf_preds),
                    "expected": round(conf_target / 100, 2)
                }
        
        response = {
            "total_predictions": len(predictions),
            "resolved_predictions": len([p for p in predictions if p.resolved_at]),
            "win_rate": round(win_rate, 4),
            "roi": round(roi, 4),
            "calibration_error": round(calibration_error, 4),
            "by_sport": by_sport,
            "confidence_bins": confidence_bins,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        if debug:
            response["_debug"] = debug_info
        
        return response
        
    except Exception as e:
        logger.error(f"Error in accuracy metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calibration")
async def get_calibration_data(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get confidence calibration curve data.
    
    Confidence should match actual accuracy (50% conf = ~50% wins).
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(Prediction).filter(
            Prediction.created_at >= cutoff_date,
            Prediction.resolved_at.isnot(None)
        )
        
        result = await db.execute(query)
        predictions = result.scalars().all()
        
        if not predictions:
            return {
                "calibration_data": [],
                "perfect_calibration": [],
                "generated_at": datetime.utcnow().isoformat()
            }
        
        # Build confidence bins
        bins = {}
        for p in predictions:
            if p.confidence is None:
                continue
            bin_key = round(p.confidence)  # 1% bins
            if bin_key not in bins:
                bins[bin_key] = {'wins': 0, 'total': 0}
            bins[bin_key]['total'] += 1
            if p.result == "win":
                bins[bin_key]['wins'] += 1
        
        # Format calibration data
        calibration_data = []
        for confidence in sorted(bins.keys()):
            data = bins[confidence]
            if data['total'] >= 5:
                actual_accuracy = data['wins'] / data['total']
                calibration_data.append({
                    "confidence": round(confidence / 100, 2),
                    "actual_accuracy": round(actual_accuracy, 2),
                    "count": data['total']
                })
        
        # Perfect calibration line
        perfect_calibration = [
            {"confidence": i / 100, "actual_accuracy": i / 100}
            for i in range(50, 101, 5)
        ]
        
        return {
            "calibration_data": calibration_data,
            "perfect_calibration": perfect_calibration,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in calibration data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions")
async def get_predictions_list(
    days: int = Query(30, ge=1, le=365),
    sport_key: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get paginated list of predictions with performance.
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(Prediction).filter(
            Prediction.created_at >= cutoff_date
        )
        
        if sport_key:
            query = query.filter(Prediction.sport_key == sport_key)
        
        # Get total count
        count_result = await db.execute(select(func.count(Prediction.id)).filter(
            Prediction.created_at >= cutoff_date
        ))
        total_count = count_result.scalar() or 0
        
        # Get paginated results
        result = await db.execute(
            query.order_by(Prediction.created_at.desc()).offset(offset).limit(limit)
        )
        predictions = result.scalars().all()
        
        predictions_list = []
        for p in predictions:
            result_status = None
            if p.resolved_at:
                result_status = "Win" if p.result else "Loss"
            
            predictions_list.append({
                "id": p.id,
                "sport_key": p.sport_key,
                "market_type": p.market_type,
                "prediction": p.prediction,
                "confidence": round(p.confidence, 1) if p.confidence else None,
                "created_at": p.created_at.isoformat(),
                "resolved_at": p.resolved_at.isoformat() if p.resolved_at else None,
                "result": result_status
            })
        
        return {
            "total": total_count,
            "offset": offset,
            "limit": limit,
            "predictions": predictions_list,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in predictions list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_analytics_summary(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Quick summary of key metrics for 7, 14, 30 days.
    """
    try:
        summary = {}
        
        for days in [7, 14, 30]:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = select(Prediction).filter(
                Prediction.created_at >= cutoff_date,
                Prediction.resolved_at.isnot(None)
            )
            
            result = await db.execute(query)
            predictions = result.scalars().all()
            
            summary[f"days_{days}"] = {
                "total": len(predictions),
                "accuracy": round(calculate_win_rate(predictions), 4),
                "roi": round(calculate_roi(predictions), 4),
                "calibration": round(calculate_calibration_error(predictions), 4)
            }
        
        return {
            "summary": summary,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platform-metrics")
async def get_platform_metrics(
    days: int = Query(30, ge=1, le=365),
    debug: bool = Query(False),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get platform-wide prediction metrics using PredictionRecords.
    
    This endpoint shows overall platform performance metrics by tracking:
    - All predictions made by all users (from PredictionRecord table)
    - Metrics for all users combined
    - Real-time stats (not waiting for resolution)
    
    Returns:
        - Platform overall accuracy 
        - Predictions by sport
        - Breakdown by outcome (hit/miss/pending)
    """
    try:
        from datetime import timezone
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        logger.info(f"[PLATFORM_METRICS] Fetching platform metrics from PredictionRecords for last {days} days (cutoff: {cutoff_date})")
        
        # Import PredictionRecord model
        from app.models.prediction_records import PredictionRecord
        
        # Get all prediction records from the platform
        query = select(PredictionRecord).filter(
            PredictionRecord.created_at >= cutoff_date
        )
        
        result = await db.execute(query)
        all_records = result.scalars().all()
        
        logger.info(f"[PLATFORM_METRICS] Found {len(all_records)} total prediction records")
        
        if not all_records:
            logger.info("[PLATFORM_METRICS] No predictions found, returning zero metrics")
            return {
                "platform_overall": {
                    "total_predictions": 0,
                    "hits": 0,
                    "misses": 0, 
                    "pending": 0,
                    "win_rate": 0.0,
                    "avg_confidence": 0.0,
                },
                "by_sport": {},
                "generated_at": datetime.utcnow().isoformat()
            }
        
        # Calculate overall platform metrics
        hits = len([r for r in all_records if r.outcome == 'hit'])
        misses = len([r for r in all_records if r.outcome == 'miss'])
        pending = len([r for r in all_records if r.outcome == 'pending'])
        voids = len([r for r in all_records if r.outcome in ['void', 'cancelled']])
        
        total_decided = hits + misses
        overall_win_rate = (hits / total_decided) if total_decided > 0 else 0.0
        
        # IMPORTANT: Normalize confidence from 0-100 to 0-1 if needed
        confidence_values = [r.confidence for r in all_records if r.confidence]
        if confidence_values:
            overall_avg_confidence = np.mean(confidence_values)
            # Normalize if in 0-100 range (if avg > 1.0, divide by 100)
            if overall_avg_confidence > 1.0:
                overall_avg_confidence = overall_avg_confidence / 100.0
        else:
            overall_avg_confidence = 0.0
        
        # By sport breakdown
        by_sport = {}
        for sport in set(r.sport_key for r in all_records if r.sport_key):
            sport_records = [r for r in all_records if r.sport_key == sport]
            sport_hits = len([r for r in sport_records if r.outcome == 'hit'])
            sport_misses = len([r for r in sport_records if r.outcome == 'miss'])
            sport_pending = len([r for r in sport_records if r.outcome == 'pending'])
            
            sport_decided = sport_hits + sport_misses
            sport_win_rate = (sport_hits / sport_decided) if sport_decided > 0 else 0.0
            
            # IMPORTANT: Normalize sport confidence the same way
            sport_confidence_values = [r.confidence for r in sport_records if r.confidence]
            if sport_confidence_values:
                sport_avg_confidence = np.mean(sport_confidence_values)
                if sport_avg_confidence > 1.0:
                    sport_avg_confidence = sport_avg_confidence / 100.0
            else:
                sport_avg_confidence = 0.0
            
            by_sport[sport] = {
                "total": len(sport_records),
                "hits": sport_hits,
                "misses": sport_misses,
                "pending": sport_pending,
                "win_rate": round(sport_win_rate, 4),
                "avg_confidence": round(sport_avg_confidence, 4),  # Return as 0-1 decimal
            }
        
        response = {
            "platform_overall": {
                "total_predictions": len(all_records),
                "hits": hits,
                "misses": misses,
                "pending": pending,
                "voids": voids,
                "win_rate": round(overall_win_rate, 4),
                "avg_confidence": round(overall_avg_confidence, 4),  # Return as 0-1 decimal
            },
            "by_sport": by_sport,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        if debug:
            response["_debug"] = {
                "total_records": len(all_records),
                "cutoff_date": str(cutoff_date),
                "outcome_breakdown": {
                    "hit": hits,
                    "miss": misses,
                    "pending": pending,
                    "void": voids
                }
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in platform metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
