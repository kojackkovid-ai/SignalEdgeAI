"""
Prediction History Service
Stores prediction records and calculates accuracy statistics
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_, Integer, cast
from app.models.prediction_records import (
    PredictionRecord, PredictionAccuracyStats, PlayerRecord,
    PlayerSeasonStats, PlayerGameLog, PlayerPropLine
)
from app.models.db_models import User
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import logging

logger = logging.getLogger(__name__)

class PredictionHistoryService:
    """Handle recording and retrieving prediction history"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def record_prediction(
        self,
        user_id: str,
        sport_key: str,
        event_id: str,
        prediction_data: Dict
    ) -> str:
        """Store a new prediction in history"""
        try:
            record = PredictionRecord(
                user_id=user_id,
                sport_key=sport_key,
                event_id=event_id,
                matchup=prediction_data.get('matchup'),
                home_team=prediction_data.get('home_team'),
                away_team=prediction_data.get('away_team'),
                prediction_type=prediction_data.get('prediction_type'),
                prediction=prediction_data.get('prediction'),
                player_name=prediction_data.get('player_name'),
                player_stat_type=prediction_data.get('stat_type'),
                line=prediction_data.get('line'),
                confidence=prediction_data.get('confidence'),
                reasoning=prediction_data.get('reasoning', []),
                model_weights=prediction_data.get('model_weights'),
                event_start_time=prediction_data.get('event_start_time'),
                created_at=datetime.utcnow(),
                outcome='pending'
            )
            self.db.add(record)
            await self.db.commit()
            logger.info(f"Recorded prediction {record.id} for user {user_id}")
            return str(record.id)  # type: ignore
        except Exception as e:
            logger.error(f"Error recording prediction: {e}")
            await self.db.rollback()
            raise
    
    async def get_user_prediction_history(
        self,
        user_id: str,
        sport_key: Optional[str] = None,
        outcome: Optional[str] = None,
        confidence_min: float = 0.0,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        """Get paginated prediction history for user"""
        query = select(PredictionRecord).where(
            PredictionRecord.user_id == user_id
        )
        
        # Apply filters
        filters = []
        if sport_key:
            filters.append(PredictionRecord.sport_key == sport_key)
        if outcome:
            filters.append(PredictionRecord.outcome == outcome)
        if confidence_min > 0:
            filters.append(PredictionRecord.confidence >= confidence_min)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Get total count
        count_query = select(func.count()).select_from(PredictionRecord).where(
            and_(
                PredictionRecord.user_id == user_id,
                *filters
            ) if filters else PredictionRecord.user_id == user_id
        )
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Order and paginate
        query = query.order_by(desc(PredictionRecord.created_at))
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        records = result.scalars().all()
        
        return [self._record_to_dict(r) for r in records], int(total_count)
    
    async def get_user_stats(self, user_id: str) -> Dict:
        """Get overall accuracy statistics for user"""
        result = await self.db.execute(
            select(PredictionAccuracyStats).where(
                and_(
                    PredictionAccuracyStats.user_id == user_id,
                    PredictionAccuracyStats.sport_key.is_(None)  # Overall stats
                )
            )
        )
        stats = result.scalars().first()
        
        if stats:
            avg_conf = stats.avg_confidence or 0.0
            # Normalize confidence from 0-100 to 0-1 if needed
            normalized_conf = (float(avg_conf) / 100.0) if avg_conf > 1.0 else float(avg_conf)
            return {
                'total': stats.total_predictions,
                'hits': stats.hits,
                'misses': stats.misses,
                'voids': stats.voids,
                'pending': stats.pending,
                'win_rate': stats.win_rate or 0.0,
                'avg_confidence': normalized_conf,
                'roi': stats.roi or 0.0,
                'last_updated': stats.last_updated.isoformat()
            }
        
        # Calculate from scratch if no cached stats
        return await self._calculate_user_stats_from_records(user_id)
    
    async def get_user_stats_by_sport(self, user_id: str) -> Dict[str, Dict]:
        """Get accuracy broken down by sport"""
        # First get totals for all predictions by sport (including pending)
        total_by_sport_result = await self.db.execute(
            select(
                PredictionRecord.sport_key,
                func.count().label('total')
            ).where(
                PredictionRecord.user_id == user_id
            ).group_by(PredictionRecord.sport_key)
        )
        
        totals_by_sport = {}
        for row in total_by_sport_result:
            totals_by_sport[row.sport_key] = row.total
        
        # Get resolved stats (hit/miss only)
        result = await self.db.execute(
            select(
                PredictionRecord.sport_key,
                func.sum(
                    func.cast(
                        PredictionRecord.outcome == 'hit',
                        Integer()
                    )
                ).label('hits'),
                func.sum(
                    func.cast(
                        PredictionRecord.outcome == 'miss',
                        Integer()
                    )
                ).label('misses')
            ).where(
                and_(
                    PredictionRecord.user_id == user_id,
                    PredictionRecord.outcome.in_(['hit', 'miss'])
                )
            ).group_by(PredictionRecord.sport_key)
        )
        
        # Get average confidence from ALL predictions per sport
        avg_conf_result = await self.db.execute(
            select(
                PredictionRecord.sport_key,
                func.avg(PredictionRecord.confidence).label('avg_conf')
            ).where(
                PredictionRecord.user_id == user_id
            ).group_by(PredictionRecord.sport_key)
        )
        
        avg_conf_by_sport = {}
        for row in avg_conf_result:
            avg_conf_by_sport[row.sport_key] = row.avg_conf
        
        sport_stats = {}
        for row in result:
            sport_key = row.sport_key
            total = totals_by_sport.get(sport_key, 0)
            hits = row.hits or 0
            misses = row.misses or 0
            win_rate = (hits / (hits + misses)) if (hits + misses) > 0 else 0.0
            avg_conf = avg_conf_by_sport.get(sport_key, 0)
            # Normalize confidence from 0-100 to 0-1 if needed
            normalized_conf = (float(avg_conf) / 100.0) if avg_conf and avg_conf > 1.0 else (float(avg_conf) if avg_conf else 0.0)
            sport_stats[sport_key] = {
                'total': total,
                'hits': hits,
                'misses': misses,
                'pending': total - hits - misses,
                'win_rate': win_rate,
                'avg_confidence': normalized_conf
            }
        
        return sport_stats
    
    async def resolve_pending_predictions(self) -> int:
        """
        Resolve predictions that have now completed.
        Called as a daily background task.
        """
        # Get all pending predictions whose games have started
        result = await self.db.execute(
            select(PredictionRecord).where(
                and_(
                    PredictionRecord.outcome == 'pending',
                    PredictionRecord.event_start_time < datetime.utcnow()
                )
            )
        )
        
        pending_preds = result.scalars().all()
        resolved_count = 0
        
        for pred in pending_preds:
            try:
                # Fetch actual game result (would call ESPN service)
                # This is a placeholder - actual implementation depends on ESPN API
                actual_result = await self._get_game_result(
                    str(pred.event_id), str(pred.sport_key)  # type: ignore
                )
                
                if actual_result:
                    # Compare prediction to actual result
                    outcome = self._compare_prediction_to_result(pred, actual_result)
                    pred.outcome = outcome  # type: ignore
                    pred.resolved_at = datetime.utcnow()  # type: ignore
                    pred.actual_result = str(actual_result)  # type: ignore
                    
                    # Update user stats
                    await self._update_user_stats(str(pred.user_id), outcome)  # type: ignore
                    resolved_count += 1
            except Exception as e:
                logger.error(f"Error resolving prediction {pred.id}: {e}")
        
        if resolved_count > 0:
            await self.db.commit()
            logger.info(f"Resolved {resolved_count} predictions")
        
        return resolved_count
    
    async def _calculate_user_stats_from_records(self, user_id: str) -> Dict:
        """Calculate accuracy stats from all prediction records"""
        # Count ALL predictions (including pending) for total
        total_result = await self.db.execute(
            select(func.count()).select_from(PredictionRecord).where(
                PredictionRecord.user_id == user_id
            )
        )
        total = total_result.scalar() or 0
        
        # Count only resolved predictions (hit/miss) for accuracy
        result = await self.db.execute(
            select(
                func.sum(
                    func.cast(
                        PredictionRecord.outcome == 'hit',
                        Integer()
                    )
                ).label('hits'),
                func.sum(
                    func.cast(
                        PredictionRecord.outcome == 'miss',
                        Integer()
                    )
                ).label('misses'),
                func.avg(PredictionRecord.confidence).label('avg_conf')
            ).where(
                and_(
                    PredictionRecord.user_id == user_id,
                    PredictionRecord.outcome.in_(['hit', 'miss'])
                )
            )
        )
        
        # Calculate average confidence from ALL predictions (not just hit/miss) - EXCLUDE club_100_access
        avg_conf_all_result = await self.db.execute(
            select(func.avg(PredictionRecord.confidence)).where(
                and_(
                    PredictionRecord.user_id == user_id,
                    PredictionRecord.sport_key != 'club_100_access'
                )
            )
        )
        avg_conf_all = avg_conf_all_result.scalar()
        
        row = result.first()
        if row is None or total == 0:
            return {
                'total': total,
                'hits': 0,
                'misses': 0,
                'pending': total,  # Show pending count
                'win_rate': 0.0,
                'avg_confidence': (float(avg_conf_all / 100.0) if avg_conf_all and avg_conf_all > 1.0 else (float(avg_conf_all) if avg_conf_all else 0.0)),
                'roi': 0.0
            }
        
        hits = row.hits or 0
        misses = row.misses or 0
        pending = total - hits - misses
        
        return {
            'total': total,
            'hits': hits,
            'misses': misses,
            'pending': pending,  # Show pending count
            'win_rate': (hits / (hits + misses)) if (hits + misses) > 0 else 0.0,
            'avg_confidence': float(avg_conf_all / 100.0) if avg_conf_all and avg_conf_all > 1.0 else (float(avg_conf_all) if avg_conf_all else 0.0),
            'roi': 0.0  # Would be calculated from actual bet amounts
        }
    
    async def _update_user_stats(self, user_id: str, outcome: str):
        """Update cached accuracy stats for user"""
        result = await self.db.execute(
            select(PredictionAccuracyStats).where(
                and_(
                    PredictionAccuracyStats.user_id == user_id,
                    PredictionAccuracyStats.sport_key.is_(None)
                )
            )
        )
        stats = result.scalars().first()
        
        if not stats:
            stats = PredictionAccuracyStats(
                user_id=user_id,
                total_predictions=0,
                hits=0,
                misses=0,
                voids=0,
                pending=0,
                win_rate=0.0,
                avg_confidence=0.0,
                roi=0.0
            )
            self.db.add(stats)
        
        # Update counts
        current_total = (stats.total_predictions or 0) if isinstance(stats.total_predictions, int) else 0  # type: ignore
        stats.total_predictions = current_total + 1  # type: ignore
        
        if outcome == 'hit':
            current_hits = (stats.hits or 0) if isinstance(stats.hits, int) else 0  # type: ignore
            stats.hits = current_hits + 1  # type: ignore
        elif outcome == 'miss':
            current_misses = (stats.misses or 0) if isinstance(stats.misses, int) else 0  # type: ignore
            stats.misses = current_misses + 1  # type: ignore
        elif outcome == 'void':
            current_voids = (stats.voids or 0) if isinstance(stats.voids, int) else 0  # type: ignore
            stats.voids = current_voids + 1  # type: ignore
        
        # Recalculate rate
        total_hits = (stats.hits or 0) if isinstance(stats.hits, int) else 0  # type: ignore
        total_misses = (stats.misses or 0) if isinstance(stats.misses, int) else 0  # type: ignore
        total_decisive = total_hits + total_misses
        stats.win_rate = (total_hits / total_decisive) if total_decisive > 0 else 0.0  # type: ignore
        stats.last_updated = datetime.utcnow()  # type: ignore
        
        await self.db.flush()
    
    async def _get_game_result(self, event_id: str, sport_key: str) -> Optional[Dict]:
        """Fetch actual game result from ESPN (placeholder)"""
        # This would be implemented with actual ESPN API calls
        # Returns something like: {home_score: 102, away_score: 98}
        return None
    
    def _compare_prediction_to_result(self, pred: PredictionRecord, actual_result: Dict) -> str:
        """Determine if prediction was hit/miss/void"""
        # This logic would depend on prediction type and actual result
        # Placeholder that just checks if prediction matched
        return 'pending'  # TODO: Implement actual comparison logic
    
    def _record_to_dict(self, record: PredictionRecord) -> Dict:
        """Convert prediction record to dictionary"""
        return {
            'id': record.id,
            'sport_key': record.sport_key,
            'matchup': record.matchup,
            'prediction': record.prediction,
            'confidence': record.confidence,
            'line': record.line,
            'created_at': record.created_at.isoformat(),
            'event_start_time': record.event_start_time.isoformat() if record.event_start_time is not None else None,  # type: ignore
            'outcome': record.outcome,
            'actual_result': record.actual_result,
            'reasoning': record.reasoning
        }


class PlayerDataService:
    """Synchronize player data from ESPN"""
    
    def __init__(self, db: AsyncSession, espn_client):
        self.db = db
        self.espn = espn_client
    
    async def sync_all_players(self, sport_key: str):
        """Fetch all players for a sport from ESPN and store"""
        logger.info(f"Syncing {sport_key} players...")
        
        try:
            players_data = await self._fetch_players_from_espn(sport_key)
            
            for player_data in players_data:
                existing = await self.db.execute(
                    select(PlayerRecord).where(
                        and_(
                            PlayerRecord.sport_key == sport_key,
                            getattr(PlayerRecord, f'{sport_key[0:3]}_id') == player_data.get('id')
                        )
                    )
                )
                existing_player = existing.scalars().first()
                
                if existing_player:
                    # Update existing
                    for key, value in player_data.items():
                        if hasattr(existing_player, key):
                            setattr(existing_player, key, value)
                else:
                    # Create new
                    new_player = PlayerRecord(**player_data)
                    self.db.add(new_player)
            
            await self.db.commit()
            logger.info(f"Synced {len(players_data)} {sport_key} players")
        except Exception as e:
            logger.error(f"Error syncing players: {e}")
            await self.db.rollback()
            raise
    
    async def _fetch_players_from_espn(self, sport_key: str) -> List[Dict]:
        """Fetch player list from ESPN API"""
        # Placeholder - would make actual ESPN calls
        return []
    
    async def sync_season_stats(self, sport_key: str, season: int):
        """Fetch season stats for all players"""
        logger.info(f"Syncing {sport_key} season {season} stats...")
        
        try:
            players = await self.db.execute(
                select(PlayerRecord).where(PlayerRecord.sport_key == sport_key)
            )
            
            for player in players.scalars():
                stats = await self._fetch_player_season_stats(player, season)
                if stats:
                    season_record = PlayerSeasonStats(
                        player_id=player.id,
                        sport_key=sport_key,
                        season=season,
                        **stats
                    )
                    self.db.add(season_record)
            
            await self.db.commit()
        except Exception as e:
            logger.error(f"Error syncing season stats: {e}")
            await self.db.rollback()
            raise
    
    async def _fetch_player_season_stats(self, player: PlayerRecord, season: int) -> Optional[Dict]:
        """Fetch season stats for a player"""
        # Placeholder - would make actual ESPN calls
        return None
