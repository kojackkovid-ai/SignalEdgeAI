"""
ML Training Dashboard Service
Comprehensive monitoring and reporting of model training pipeline
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.db_models import (
    TrainingSession,
    ModelPerformanceMetrics,
    ScheduledTrainingJob
)
from app.models.prediction_records import PredictionRecord

logger = logging.getLogger(__name__)


class MLTrainingDashboard:
    """
    Comprehensive dashboard for ML training pipeline monitoring
    Provides overview of:
    - Current training status
    - Model health across all sports
    - Performance trends
    - Drift detection alerts
    - Training schedule
    """
    
    async def get_dashboard_summary(self, session: AsyncSession) -> Dict:
        """
        Get comprehensive dashboard summary
        
        Returns:
            Dict with:
            - scheduler_status: Is scheduler running
            - recent_trainings: Last 5 training sessions
            - model_health: Health status for each model
            - alerts: Active drift/performance alerts
            - metrics: Key platform metrics
        """
        try:
            summary = {
                'timestamp': datetime.utcnow().isoformat(),
                'scheduler_status': await self._get_scheduler_status(session),
                'training_summary': await self._get_training_summary(session),
                'model_health_overview': await self._get_model_health_overview(session),
                'active_alerts': await self._get_active_alerts(session),
                'platform_metrics': await self._get_platform_metrics(session),
                'scheduled_jobs': await self._get_scheduled_jobs_summary(session)
            }
            return summary
        except Exception as e:
            logger.error(f"Error generating dashboard summary: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _get_scheduler_status(self, session: AsyncSession) -> Dict:
        """Get scheduler operational status"""
        try:
            # Count active jobs
            result = await session.execute(
                select(func.count(ScheduledTrainingJob.id)).where(
                    ScheduledTrainingJob.is_enabled == True
                )
            )
            active_jobs = result.scalar() or 0
            
            # Get next scheduled run
            result = await session.execute(
                select(ScheduledTrainingJob.next_run_at).where(
                    ScheduledTrainingJob.is_enabled == True
                ).order_by(ScheduledTrainingJob.next_run_at).limit(1)
            )
            next_run = result.scalar()
            
            return {
                'status': 'running' if active_jobs > 0 else 'idle',
                'active_jobs': active_jobs,
                'next_scheduled_run': next_run.isoformat() if next_run else None,
                'last_check': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def _get_training_summary(self, session: AsyncSession) -> Dict:
        """Get summary of recent training sessions"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            
            # Get recent trainings
            result = await session.execute(
                select(TrainingSession).where(
                    TrainingSession.created_at >= cutoff_time
                ).order_by(desc(TrainingSession.started_at)).limit(10)
            )
            recent_sessions = result.scalars().all()
            
            # Statistics
            total_trainings = len(recent_sessions)
            successful = sum(1 for s in recent_sessions if s.status == 'completed')
            failed = sum(1 for s in recent_sessions if s.status == 'failed')
            running = sum(1 for s in recent_sessions if s.status == 'in_progress')
            
            # Average accuracy
            accuracies = [s.validation_accuracy for s in recent_sessions if s.validation_accuracy]
            avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else None
            
            return {
                'period_days': 7,
                'total_trainings': total_trainings,
                'successful': successful,
                'failed': failed,
                'running': running,
                'average_validation_accuracy': avg_accuracy,
                'recent_sessions': [
                    {
                        'id': s.id,
                        'sport_key': s.sport_key,
                        'market_type': s.market_type,
                        'status': s.status,
                        'started_at': s.started_at.isoformat(),
                        'completed_at': s.completed_at.isoformat() if s.completed_at else None,
                        'duration_seconds': s.duration_seconds,
                        'validation_accuracy': s.validation_accuracy,
                        'trigger_reason': s.trigger_reason
                    }
                    for s in recent_sessions[:5]
                ]
            }
        except Exception as e:
            logger.error(f"Error getting training summary: {e}")
            return {'error': str(e)}
    
    async def _get_model_health_overview(self, session: AsyncSession) -> Dict:
        """Get health overview of all models"""
        try:
            result = await session.execute(
                select(ScheduledTrainingJob).where(ScheduledTrainingJob.is_enabled == True)
            )
            jobs = result.scalars().all()
            
            health_by_status = {'healthy': 0, 'warning': 0, 'critical': 0}
            model_healths = []
            
            for job in jobs:
                # Get last training for this model
                result = await session.execute(
                    select(TrainingSession).where(
                        and_(
                            TrainingSession.sport_key == job.sport_key,
                            TrainingSession.market_type == job.market_type,
                            TrainingSession.status == 'completed'
                        )
                    ).order_by(desc(TrainingSession.completed_at)).limit(1)
                )
                last_training = result.scalars().first()
                
                # Get recent performance metrics
                cutoff = datetime.utcnow() - timedelta(days=7)
                result = await session.execute(
                    select(ModelPerformanceMetrics).where(
                        and_(
                            ModelPerformanceMetrics.sport_key == job.sport_key,
                            ModelPerformanceMetrics.market_type == job.market_type,
                            ModelPerformanceMetrics.measurement_date >= cutoff
                        )
                    ).order_by(desc(ModelPerformanceMetrics.measurement_date)).limit(1)
                )
                latest_metrics = result.scalars().first()
                
                # Determine health status
                status = 'unknown'
                if latest_metrics:
                    if latest_metrics.has_drift:
                        status = 'critical' if latest_metrics.drift_severity == 'high' else 'warning'
                        health_by_status['critical' if status == 'critical' else 'warning'] += 1
                    elif latest_metrics.accuracy is not None and latest_metrics.accuracy < 0.55:
                        status = 'warning'
                        health_by_status['warning'] += 1
                    else:
                        status = 'healthy'
                        health_by_status['healthy'] += 1
                
                model_healths.append({
                    'sport_key': job.sport_key,
                    'market_type': job.market_type,
                    'status': status,
                    'last_trained_at': last_training.completed_at.isoformat() if last_training else None,
                    'last_accuracy': latest_metrics.accuracy if latest_metrics else None,
                    'has_drift': latest_metrics.has_drift if latest_metrics else False,
                    'days_since_training': (datetime.utcnow() - last_training.completed_at).days if last_training else None
                })
            
            return {
                'total_models': len(jobs),
                'health_counts': health_by_status,
                'models': model_healths
            }
        except Exception as e:
            logger.error(f"Error getting model health overview: {e}")
            return {'error': str(e)}
    
    async def _get_active_alerts(self, session: AsyncSession) -> List[Dict]:
        """Get active performance drift and training alerts"""
        try:
            alerts = []
            
            # Check for models with drift
            cutoff = datetime.utcnow() - timedelta(days=3)
            result = await session.execute(
                select(ModelPerformanceMetrics).where(
                    and_(
                        ModelPerformanceMetrics.has_drift == True,
                        ModelPerformanceMetrics.measurement_date >= cutoff
                    )
                )
            )
            drift_metrics = result.scalars().all()
            
            for metric in drift_metrics[:5]:  # Top 5 alerts
                alerts.append({
                    'type': 'performance_drift',
                    'severity': metric.drift_severity or 'medium',
                    'model': f"{metric.sport_key}/{metric.market_type}",
                    'detected_at': metric.measurement_date.isoformat(),
                    'message': f"Performance drift detected for {metric.sport_key}/{metric.market_type}: accuracy={metric.accuracy:.2%}",
                    'recommended_action': 'Trigger immediate retraining'
                })
            
            # Check for models not trained recently
            cutoff = datetime.utcnow() - timedelta(days=14)
            result = await session.execute(
                select(ScheduledTrainingJob).where(
                    and_(
                        ScheduledTrainingJob.is_enabled == True,
                        (ScheduledTrainingJob.last_run_at == None) | (ScheduledTrainingJob.last_run_at <= cutoff)
                    )
                )
            )
            stale_jobs = result.scalars().all()
            
            for job in stale_jobs[:3]:
                alerts.append({
                    'type': 'stale_model',
                    'severity': 'high',
                    'model': f"{job.sport_key}/{job.market_type}",
                    'last_trained': job.last_run_at.isoformat() if job.last_run_at else 'Never',
                    'message': f"Model {job.sport_key}/{job.market_type} has not been trained in over 14 days",
                    'recommended_action': 'Schedule immediate retraining'
                })
            
            return alerts
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    async def _get_platform_metrics(self, session: AsyncSession) -> Dict:
        """Get platform-wide prediction metrics"""
        try:
            cutoff = datetime.utcnow() - timedelta(days=7)
            
            result = await session.execute(
                select(PredictionRecord).where(
                    PredictionRecord.created_at >= cutoff
                )
            )
            predictions = result.scalars().all()
            
            if not predictions:
                return {
                    'predictions_7d': 0,
                    'hit_rate_7d': 0,
                    'roi_7d': 0
                }
            
            hits = sum(1 for p in predictions if p.outcome == 'hit')
            misses = sum(1 for p in predictions if p.outcome == 'miss')
            total = len([p for p in predictions if p.outcome in ['hit', 'miss']])
            
            hit_rate = (hits / total * 100) if total > 0 else 0
            
            return {
                'predictions_7d': len(predictions),
                'resolved_7d': total,
                'hits_7d': hits,
                'misses_7d': misses,
                'hit_rate_7d': f"{hit_rate:.1f}%",
                'average_confidence': sum(p.confidence for p in predictions if p.confidence) / len([p for p in predictions if p.confidence]) if predictions else 0
            }
        except Exception as e:
            logger.error(f"Error getting platform metrics: {e}")
            return {'error': str(e)}
    
    async def _get_scheduled_jobs_summary(self, session: AsyncSession) -> Dict:
        """Get summary of scheduled training jobs"""
        try:
            result = await session.execute(select(ScheduledTrainingJob))
            jobs = result.scalars().all()
            
            enabled = sum(1 for j in jobs if j.is_enabled)
            disabled = len(jobs) - enabled
            
            return {
                'total_jobs': len(jobs),
                'enabled': enabled,
                'disabled': disabled,
                'next_runs': [
                    {
                        'job_name': j.job_name,
                        'sport_key': j.sport_key,
                        'market_type': j.market_type,
                        'next_run': j.next_run_at.isoformat() if j.next_run_at else 'Not scheduled',
                        'schedule': f"Weekly on {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][j.day_of_week]} at {j.hour_utc:02d}:{j.minute_utc:02d} UTC" if j.schedule_type == 'weekly' else j.schedule_type,
                        'status': 'enabled' if j.is_enabled else 'disabled'
                    }
                    for j in sorted(jobs, key=lambda x: x.next_run_at or datetime.max)[:5]
                ]
            }
        except Exception as e:
            logger.error(f"Error getting scheduled jobs summary: {e}")
            return {'error': str(e)}
    
    async def get_model_performance_trend(
        self,
        session: AsyncSession,
        sport_key: str,
        market_type: str,
        days: int = 30
    ) -> Dict:
        """Get performance trend for a specific model over time"""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            result = await session.execute(
                select(ModelPerformanceMetrics).where(
                    and_(
                        ModelPerformanceMetrics.sport_key == sport_key,
                        ModelPerformanceMetrics.market_type == market_type,
                        ModelPerformanceMetrics.measurement_date >= cutoff
                    )
                ).order_by(ModelPerformanceMetrics.measurement_date)
            )
            metrics = result.scalars().all()
            
            if not metrics:
                return {
                    'model': f"{sport_key}/{market_type}",
                    'message': 'No performance data available',
                    'data': []
                }
            
            # Calculate trend statistics
            accuracies = [m.accuracy for m in metrics if m.accuracy is not None]
            
            return {
                'model': f"{sport_key}/{market_type}",
                'period_days': days,
                'data_points': len(metrics),
                'current_accuracy': metrics[-1].accuracy if metrics else None,
                'average_accuracy': sum(accuracies) / len(accuracies) if accuracies else None,
                'best_accuracy': max(accuracies) if accuracies else None,
                'worst_accuracy': min(accuracies) if accuracies else None,
                'trend': 'improving' if len(accuracies) > 1 and accuracies[-1] > accuracies[0] else 'declining',
                'metrics': [
                    {
                        'date': m.measurement_date.isoformat(),
                        'accuracy': m.accuracy,
                        'predictions': m.predictions_count,
                        'hits': m.hit_count,
                        'misses': m.miss_count,
                        'confidence_mean': m.confidence_mean,
                        'has_drift': m.has_drift,
                        'drift_severity': m.drift_severity
                    }
                    for m in metrics
                ]
            }
        except Exception as e:
            logger.error(f"Error getting performance trend: {e}")
            return {'error': str(e)}


# Singleton instance
_dashboard_instance = None


async def get_dashboard() -> MLTrainingDashboard:
    """Get or create dashboard singleton"""
    global _dashboard_instance
    if _dashboard_instance is None:
        _dashboard_instance = MLTrainingDashboard()
    return _dashboard_instance
