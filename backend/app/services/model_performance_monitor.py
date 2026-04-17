"""
Model Performance Monitoring Service
Tracks model performance metrics and detects performance drift
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.db_models import (
    ModelPerformanceMetrics,
    TrainingSession,
    Prediction
)

logger = logging.getLogger(__name__)


class ModelPerformanceMonitor:
    """
    Monitor ML model performance and detect performance drift
    Tracks metrics like accuracy, confidence, and ROI over time
    """
    
    def __init__(self, drift_threshold: float = 0.05):
        """
        Initialize monitor
        
        Args:
            drift_threshold: Accuracy drop threshold to trigger drift alert (default: 5%)
        """
        self.drift_threshold = drift_threshold
        self.baseline_accuracy: Dict[Tuple[str, str], float] = {}  # (sport_key, market_type) -> accuracy
        
    async def record_predictions_batch(
        self,
        session: AsyncSession,
        sport_key: str,
        market_type: str,
        window_start: datetime,
        window_end: datetime
    ) -> Optional[ModelPerformanceMetrics]:
        """
        Record prediction performance for a time window
        
        Args:
            session: Database session
            sport_key: Sport key (e.g., 'basketball_nba')
            market_type: Market type (e.g., 'moneyline')
            window_start: Start of measurement window
            window_end: End of measurement window
            
        Returns:
            ModelPerformanceMetrics record or None if no predictions
        """
        try:
            # Query predictions resolved in this window
            result = await session.execute(
                select(Prediction).where(
                    and_(
                        Prediction.sport_key == sport_key,
                        Prediction.market_key == market_type if market_type else True,
                        Prediction.resolved_at.between(window_start, window_end)
                    )
                )
            )
            records = result.scalars().all()
            
            if not records:
                logger.debug(f"No predictions found for {sport_key}/{market_type} in window")
                return None
            
            # Calculate metrics
            hit_count = sum(1 for r in records if r.outcome == 'hit')
            miss_count = sum(1 for r in records if r.outcome == 'miss')
            accuracy = hit_count / len(records) if records else 0
            
            # Calculate confidence stats
            confidences = [r.confidence for r in records if r.confidence is not None]
            confidence_mean = sum(confidences) / len(confidences) if confidences else 0
            confidence_std = self._calculate_std(confidences, confidence_mean) if confidences else 0
            
            # Calculate ROI (if we have odds data)
            roi = await self._calculate_roi(records)
            
            # Create metrics record
            metrics = ModelPerformanceMetrics(
                sport_key=sport_key,
                market_type=market_type,
                measurement_date=datetime.utcnow(),
                window_start=window_start,
                window_end=window_end,
                predictions_count=len(records),
                hit_count=hit_count,
                miss_count=miss_count,
                accuracy=accuracy,
                confidence_mean=confidence_mean,
                confidence_std=confidence_std,
                profitable_units=None,  # TODO: Calculate if odds available
                roi=roi,
                has_drift=False  # Will be updated by drift detection
            )
            
            session.add(metrics)
            await session.commit()
            
            logger.info(
                f"Recorded metrics for {sport_key}/{market_type}: "
                f"accuracy={accuracy:.2%}, samples={len(records)}, roi={roi}"
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error recording performance metrics: {e}")
            return None
    
    async def detect_drift(
        self,
        session: AsyncSession,
        sport_key: str,
        market_type: str,
        lookback_days: int = 7
    ) -> Dict[str, any]:
        """
        Detect performance drift by comparing recent performance to baseline
        
        Args:
            session: Database session
            sport_key: Sport key
            market_type: Market type
            lookback_days: Number of days to analyze
            
        Returns:
            Dict with drift detection results
        """
        try:
            # Get recent metrics
            cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
            result = await session.execute(
                select(ModelPerformanceMetrics).where(
                    and_(
                        ModelPerformanceMetrics.sport_key == sport_key,
                        ModelPerformanceMetrics.market_type == market_type,
                        ModelPerformanceMetrics.measurement_date >= cutoff_date
                    )
                ).order_by(ModelPerformanceMetrics.measurement_date)
            )
            metrics = result.scalars().all()
            
            if not metrics or len(metrics) < 2:
                return {
                    'has_drift': False,
                    'reason': 'Insufficient historical data',
                    'samples_analyzed': len(metrics) if metrics else 0
                }
            
            # Calculate average accuracy
            accuracies = [m.accuracy for m in metrics]
            recent_avg = sum(accuracies) / len(accuracies)
            recent_std = self._calculate_std(accuracies, recent_avg)
            
            # Get baseline (older metrics than lookback period)
            baseline_result = await session.execute(
                select(ModelPerformanceMetrics).where(
                    and_(
                        ModelPerformanceMetrics.sport_key == sport_key,
                        ModelPerformanceMetrics.market_type == market_type,
                        ModelPerformanceMetrics.measurement_date < cutoff_date
                    )
                ).order_by(ModelPerformanceMetrics.measurement_date.desc())
            )
            baseline_metrics = baseline_result.scalars().all()
            
            baseline_accuracy = None
            if baseline_metrics:
                baselines = [m.accuracy for m in baseline_metrics[:10]]  # Use last 10 before window
                baseline_accuracy = sum(baselines) / len(baselines) if baselines else None
            
            # Detect drift
            has_drift = False
            drift_severity = None
            reason = None
            
            if baseline_accuracy is not None:
                accuracy_drop = baseline_accuracy - recent_avg
                
                if accuracy_drop >= self.drift_threshold:
                    has_drift = True
                    
                    if accuracy_drop >= 0.15:
                        drift_severity = 'high'
                        reason = f'Accuracy dropped {accuracy_drop:.1%} (baseline: {baseline_accuracy:.1%} → recent: {recent_avg:.1%})'
                    elif accuracy_drop >= 0.10:
                        drift_severity = 'medium'
                        reason = f'Accuracy dropped {accuracy_drop:.1%}'
                    else:
                        drift_severity = 'low'
                        reason = f'Accuracy dropped {accuracy_drop:.1%}'
            
            # Check for low confidence (possible model uncertainty)
            recent_confidences = [m.confidence_mean for m in metrics if m.confidence_mean]
            if recent_confidences:
                avg_confidence = sum(recent_confidences) / len(recent_confidences)
                if avg_confidence < 0.55:  # Below 55% threshold
                    if not has_drift:
                        has_drift = True
                        drift_severity = 'low'
                        reason = f'Low average confidence: {avg_confidence:.1%}'
                    else:
                        reason += f' + low confidence ({avg_confidence:.1%})'
            
            # Update metrics with drift flag
            if has_drift:
                for metric in metrics[-3:]:  # Flag recent metrics
                    metric.has_drift = True
                    metric.drift_severity = drift_severity
                await session.commit()
            
            return {
                'has_drift': has_drift,
                'drift_severity': drift_severity,
                'reason': reason,
                'recent_accuracy': recent_avg,
                'baseline_accuracy': baseline_accuracy,
                'samples_analyzed': len(metrics)
            }
            
        except Exception as e:
            logger.error(f"Error detecting drift for {sport_key}/{market_type}: {e}")
            return {'has_drift': False, 'reason': f'Error: {e}'}
    
    async def get_model_health(
        self,
        session: AsyncSession,
        sport_key: str,
        market_type: str,
        days: int = 7
    ) -> Dict[str, any]:
        """
        Get comprehensive health report for a model
        
        Args:
            session: Database session
            sport_key: Sport key
            market_type: Market type
            days: Number of days to analyze
            
        Returns:
            Health report with metrics and recommendations
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get metrics
            result = await session.execute(
                select(ModelPerformanceMetrics).where(
                    and_(
                        ModelPerformanceMetrics.sport_key == sport_key,
                        ModelPerformanceMetrics.market_type == market_type,
                        ModelPerformanceMetrics.measurement_date >= cutoff_date
                    )
                ).order_by(ModelPerformanceMetrics.measurement_date)
            )
            metrics = result.scalars().all()
            
            # Get latest training session
            training_result = await session.execute(
                select(TrainingSession).where(
                    and_(
                        TrainingSession.sport_key == sport_key,
                        TrainingSession.market_type == market_type,
                        TrainingSession.status == 'completed'
                    )
                ).order_by(TrainingSession.completed_at.desc())
            )
            latest_training = training_result.scalars().first()
            
            if not metrics:
                return {
                    'status': 'no_data',
                    'message': 'No recent predictions for this model'
                }
            
            # Calculate aggregates
            total_predictions = sum(m.predictions_count for m in metrics)
            total_hits = sum(m.hit_count for m in metrics)
            avg_accuracy = sum(m.accuracy * m.predictions_count for m in metrics) / total_predictions if total_predictions else 0
            avg_confidence = sum(m.confidence_mean for m in metrics) / len(metrics)
            
            # Determine health status
            if total_hits == 0 or avg_accuracy < 0.50:
                health_status = 'critical'
            elif avg_accuracy < 0.55:
                health_status = 'poor'
            elif avg_accuracy < 0.60:
                health_status = 'fair'
            else:
                health_status = 'good'
            
            # Recommendations
            recommendations = []
            if avg_accuracy < 0.55:
                recommendations.append('Model accuracy below 55% - recommend retraining')
            if avg_confidence < 0.55:
                recommendations.append('Model showing uncertainty - check data quality')
            if latest_training and (datetime.utcnow() - latest_training.completed_at) > timedelta(days=14):
                recommendations.append('Model not retrained in 14+ days - schedule retraining')
            
            return {
                'status': health_status,
                'sport_key': sport_key,
                'market_type': market_type,
                'period_days': days,
                'metrics': {
                    'total_predictions': total_predictions,
                    'total_hits': total_hits,
                    'accuracy': avg_accuracy,
                    'avg_confidence': avg_confidence,
                    'winning_percentage': (total_hits / total_predictions * 100) if total_predictions else 0
                },
                'last_training': {
                    'completed_at': latest_training.completed_at.isoformat() if latest_training else None,
                    'accuracy': latest_training.validation_accuracy if latest_training else None,
                    'samples_used': latest_training.training_samples if latest_training else None
                } if latest_training else None,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error getting model health for {sport_key}/{market_type}: {e}")
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def _calculate_std(values: List[float], mean: float) -> float:
        """Calculate standard deviation"""
        if not values or len(values) < 2:
            return 0
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    @staticmethod
    async def _calculate_roi(records: List) -> float:
        """Calculate ROI from prediction records"""
        # TODO: Implement ROI calculation once odds data is available
        return None


# Global monitor instance
_monitor = None

async def get_model_monitor() -> ModelPerformanceMonitor:
    """Get or create global monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = ModelPerformanceMonitor()
    return _monitor
