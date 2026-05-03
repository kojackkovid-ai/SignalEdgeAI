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
            
            self.stats['total_resolved'] += resolved_count
            self.stats['last_run'] = start_time
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"✅ Resolved {resolved_count} predictions in {duration:.2f}s")
            
            return {
                'success': True,
                'resolved_count': resolved_count,
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
            # ROI calculation: edge above breakeven at standard -110 juice
            # Breakeven win rate for -110 = 11/21 ≈ 52.38%
            # Formula: (win_rate - 0.5238) / 0.5238 * 100 → % edge vs breakeven
            BREAKEVEN = 11 / 21  # ≈ 0.5238 for -110 standard juice
            user.roi = ((win_rate - BREAKEVEN) / BREAKEVEN * 100) if total > 0 else 0.0
            
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
