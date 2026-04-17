"""
Prediction Resolution Background Task Service
Automatically resolves predictions based on ESPN/live data
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db_models import Prediction, User
from app.services.prediction_service import PredictionService
from sqlalchemy import select, func, and_, Integer

logger = logging.getLogger(__name__)


class PredictionResolutionService:
    """Service to automatically resolve predictions in the background"""
    
    def __init__(self):
        self.prediction_service = PredictionService()
        self.stats = {
            'total_resolved': 0,
            'total_failed': 0,
            'last_run': None,
            'next_run': None,
        }
    
    async def resolve_all_pending_predictions(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Main task: Resolve all unresolved predictions
        Call this periodically (hourly recommended)
        """
        start_time = datetime.utcnow()
        logger.info("🔄 Starting prediction resolution task...")
        
        try:
            resolved_count = await self.prediction_service.resolve_predictions(db)
            await self._update_user_stats(db)
            
            # CRITICAL: Also sync resolved outcomes to PredictionRecord table (for accuracy dashboard)
            synced_count = await self._sync_predictions_to_history(db)
            logger.info(f"📊 Synced {synced_count} resolved predictions to PredictionRecord")
            
            self.stats['total_resolved'] += resolved_count
            self.stats['last_run'] = start_time
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"✅ Resolved {resolved_count} predictions & synced {synced_count} records in {duration:.2f}s")
            
            return {
                'success': True,
                'resolved_count': resolved_count,
                'synced_count': synced_count,
                'duration_seconds': duration,
                'timestamp': start_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error resolving predictions: {e}", exc_info=True)
            self.stats['total_failed'] += 1
            
            return {
                'success': False,
                'error': str(e),
                'timestamp': start_time.isoformat()
            }
    
    async def _sync_predictions_to_history(self, db: AsyncSession) -> int:
        """
        Sync resolved Predictions to PredictionRecord table for accuracy dashboard.
        This is CRITICAL for the accuracy dashboard to work!
        Maps: win → hit, loss → miss, push → void
        """
        try:
            from app.models.db_models import Prediction
            from app.models.prediction_records import PredictionRecord
            from sqlalchemy import and_
            
            logger.info("🔄 Starting sync of resolved Predictions to PredictionRecord...")
            
            # Get all recently resolved Predictions that haven't been synced yet
            # We look for predictions that have result set but corresponding PredictionRecord still has outcome='pending'
            result = await db.execute(
                select(Prediction).where(
                    and_(
                        Prediction.result != None,
                        Prediction.resolved_at != None,
                        Prediction.event_id != None
                    )
                )
            )
            resolved_predictions = result.scalars().all()
            logger.info(f"Found {len(resolved_predictions)} resolved Predictions to sync")
            
            synced_count = 0
            
            for pred in resolved_predictions:
                try:
                    # Find matching PredictionRecord(s) by event_id
                    records_result = await db.execute(
                        select(PredictionRecord).where(
                            and_(
                                PredictionRecord.event_id == pred.event_id,
                                PredictionRecord.outcome == 'pending'
                            )
                        )
                    )
                    records = records_result.scalars().all()
                    
                    # Map Prediction result to PredictionRecord outcome
                    outcome_map = {
                        'win': 'hit',
                        'loss': 'miss',
                        'push': 'void'
                    }
                    
                    # Get the actual result value (win/loss/push)
                    pred_result = getattr(pred, 'result', None)
                    new_outcome = outcome_map.get(pred_result, 'void') if pred_result else 'void'
                    
                    logger.info(f"📝 Syncing Prediction {pred.id}: result='{pred_result}' → PredictionRecord outcome='{new_outcome}' (found {len(records)} records)")
                    
                    # Update all pending records for this event
                    for record in records:
                        record.outcome = new_outcome  # type: ignore
                        record.resolved_at = getattr(pred, 'resolved_at', datetime.utcnow())  # type: ignore
                        actual_val = getattr(pred, 'actual_value', None)
                        record.actual_result = str(actual_val) if actual_val is not None else None  # type: ignore
                        synced_count += 1
                        logger.info(f"✅ Synced prediction {pred.id} (event {pred.event_id}) → outcome: {new_outcome}")
                
                except Exception as e:
                    logger.warning(f"⚠️ Failed to sync prediction {pred.id}: {e}", exc_info=True)
            
            if synced_count > 0:
                await db.commit()
                logger.info(f"📝 Successfully synced {synced_count} predictions to PredictionRecord")
            
            return synced_count
            
        except Exception as e:
            logger.error(f"Error syncing predictions to history: {e}")
            return 0
    
    async def _update_user_stats(self, db: AsyncSession):
        """Update user win_rate, roi, and total_predictions based on resolved predictions"""
        logger.info("📊 Updating user statistics...")
        
        try:
            from app.models.prediction_records import PredictionRecord
            
            # Get all users with at least one resolved prediction
            result = await db.execute(
                select(User.id).distinct().where(
                    User.id.in_(
                        select(PredictionRecord.user_id).where(
                            PredictionRecord.outcome.in_(['hit', 'miss', 'void', 'cancelled'])
                        )
                    )
                )
            )
            user_ids = result.scalars().all()
            
            for user_id in user_ids:
                try:
                    await self._update_single_user_stats(db, user_id)
                except Exception as e:
                    logger.warning(f"Failed to update stats for user {user_id}: {e}")
            
            logger.info(f"✅ Updated stats for {len(user_ids)} users")
            
        except Exception as e:
            logger.error(f"Error updating user stats: {e}")
    
    async def _update_single_user_stats(self, db: AsyncSession, user_id: str):
        """Update win_rate, roi, total_predictions for a specific user"""
        from app.models.prediction_records import PredictionRecord
        
        # Get resolved predictions
        result = await db.execute(
            select(
                func.count().label('total'),
                func.sum(func.cast(PredictionRecord.outcome == 'hit', Integer())).label('hits'),
            ).where(
                PredictionRecord.user_id == user_id,
                PredictionRecord.outcome.in_(['hit', 'miss'])
            )
        )
        row = result.first()
        
        total = row.total or 0
        hits = row.hits or 0
        # Store win_rate as decimal 0-1, not percentage
        win_rate = (hits / total) if total > 0 else 0.0
        
        # Get user and update
        user = await db.get(User, user_id)
        if user:
            user.total_predictions = total
            user.win_rate = win_rate  # Decimal 0-1
            # ROI calculation: convert to percentage for readability (0-100)
            # Formula: (win_rate - 0.50) / 0.50 * 100
            user.roi = ((win_rate - 0.50) / 0.50 * 100) if total > 0 else 0.0
            
            db.add(user)
            await db.commit()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            **self.stats,
            'timestamp': datetime.utcnow().isoformat()
        }


async def run_prediction_resolution_loop(db_session_maker):
    """
    Background loop that resolves predictions hourly
    Should be started in app.on_event("startup")
    
    Usage:
        asyncio.create_task(
            run_prediction_resolution_loop(
                SessionLocal  # or async_session_maker
            )
        )
    """
    service = PredictionResolutionService()
    logger.info("🚀 Starting prediction resolution background loop...")
    
    while True:
        try:
            # Create new session for this iteration
            async with db_session_maker() as db:
                result = await service.resolve_all_pending_predictions(db)
                
                if result['success']:
                    logger.info(f"Resolution loop: {result['resolved_count']} predictions resolved")
                else:
                    logger.error(f"Resolution loop error: {result['error']}")
            
            # Wait 1 hour before next resolution
            # (match times vary but most games finish within an hour of scheduling)
            await asyncio.sleep(3600)
            
        except asyncio.CancelledError:
            logger.info("Prediction resolution loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error in prediction resolution loop: {e}")
            # Wait 5 minutes on error and retry
            await asyncio.sleep(300)
