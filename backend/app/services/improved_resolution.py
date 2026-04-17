"""
Improved Prediction Resolution Service
Enhanced resolution logic with better matching, logging, and error handling
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.db_models import Prediction, User
import difflib  # Built-in string matching

logger = logging.getLogger(__name__)


class ImprovedResolutionService:
    """
    Improved resolution service with:
    - Better team name matching using string similarity
    - Comprehensive logging for debugging
    - Fallback resolution strategies
    - Direct updates to PredictionRecord for sync
    """
    
    def __init__(self, espn_service):
        self.espn_service = espn_service
        self.min_match_score = 0.70  # String match threshold (0-1)
    
    async def resolve_pending_predictions(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Main resolution method. Returns stats on resolution attempts.
        """
        start_time = datetime.utcnow()
        resolved_count = 0
        failed_count = 0
        
        try:
            logger.info("=" * 60)
            logger.info("🔄 STARTING ENHANCED PREDICTION RESOLUTION")
            logger.info("=" * 60)
            
            # Get all unresolved predictions
            result = await db.execute(
                select(Prediction).where(
                    (Prediction.resolved_at == None) & 
                    (Prediction.result == None)
                )
            )
            pending_predictions = result.scalars().all()
            logger.info(f"📊 Found {len(pending_predictions)} pending predictions to resolve")
            
            if not pending_predictions:
                logger.info("✅ No pending predictions to resolve")
                return {
                    'success': True,
                    'resolved': 0,
                    'failed': 0,
                    'duration_seconds': (datetime.utcnow() - start_time).total_seconds()
                }
            
            # Group predictions by sport for efficient API calls
            predictions_by_sport = self._group_by_sport(pending_predictions)
            logger.info(f"📋 Grouped into {len(predictions_by_sport)} sports")
            
            # Try to resolve each prediction
            for sport_key, preds in predictions_by_sport.items():
                logger.info(f"\n⚽ Processing {sport_key} ({len(preds)} predictions)")
                
                try:
                    games = await self._fetch_completed_games(sport_key)
                    logger.info(f"   📥 Fetched {len(games)} completed games for {sport_key}")
                    
                    for pred in preds:
                        try:
                            matched_game = self._find_matching_game(pred, games)
                            if matched_game:
                                resolved = await self._resolve_prediction(db, pred, matched_game)
                                if resolved:
                                    resolved_count += 1
                                    logger.info(f"   ✅ Resolved: {pred.matchup} → {pred.result}")
                                else:
                                    failed_count += 1
                                    logger.warning(f"   ❌ Failed to save resolution for {pred.matchup}")
                            else:
                                logger.debug(f"   ⏳ No matching game found for {pred.matchup}")
                        except Exception as e:
                            failed_count += 1
                            logger.error(f"   ❌ Error resolving {pred.matchup}: {e}", exc_info=False)
                
                except Exception as e:
                    logger.error(f"❌ Error processing {sport_key}: {e}", exc_info=True)
                    continue
            
            # Update user stats
            try:
                await self._update_user_stats(db)
                logger.info("📊 Updated user statistics")
            except Exception as e:
                logger.warning(f"Failed to update user stats: {e}")
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info("=" * 60)
            logger.info(f"✅ RESOLUTION COMPLETE: {resolved_count} resolved, {failed_count} failed in {duration:.2f}s")
            logger.info("=" * 60)
            
            return {
                'success': True,
                'resolved': resolved_count,
                'failed': failed_count,
                'duration_seconds': duration
            }
            
        except Exception as e:
            logger.error(f"🔥 CRITICAL ERROR in resolution: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'resolved': resolved_count,
                'failed': failed_count,
                'duration_seconds': (datetime.utcnow() - start_time).total_seconds()
            }
    
    def _group_by_sport(self, predictions: List[Prediction]) -> Dict[str, List[Prediction]]:
        """Group predictions by sport_key for efficient API calls"""
        by_sport = {}
        
        for pred in predictions:
            # Try to get sport_key, fallback to mapping from sport
            sport_key = pred.sport_key
            
            if not sport_key and pred.sport:
                # Map from display name to sport_key
                sport_key = self._get_sport_key(pred.sport, pred.league)
            
            if sport_key:
                if sport_key not in by_sport:
                    by_sport[sport_key] = []
                by_sport[sport_key].append(pred)
                logger.debug(f"   📋 Grouped {pred.matchup} under {sport_key}")
        
        return by_sport
    
    def _get_sport_key(self, sport: str, league: Optional[str] = None) -> Optional[str]:
        """Convert display sport name to API sport_key"""
        mapping = {
            "NBA": "basketball_nba",
            "NFL": "americanfootball_nfl",
            "NHL": "icehockey_nhl",
            "MLB": "baseball_mlb",
            "Soccer": "soccer_usa_mls" if league and "MLS" in league else "soccer_epl"
        }
        return mapping.get(sport)
    
    async def _fetch_completed_games(self, sport_key: str) -> List[Dict]:
        """Fetch completed games for a sport"""
        games = []
        
        # Check today and yesterday for completed games
        dates = [
            datetime.utcnow().strftime("%Y%m%d"),
            (datetime.utcnow() - timedelta(days=1)).strftime("%Y%m%d")
        ]
        
        for date_str in dates:
            try:
                logger.debug(f"   🔍 Fetching games for {sport_key} on {date_str}")
                result = await self.espn_service.get_scoreboard(sport_key, date_str)
                
                if result:
                    # Filter to completed games only
                    completed = [g for g in result if g.get('completed', False)]
                    logger.debug(f"   ✓ Got {len(completed)} completed games from {len(result)} total")
                    games.extend(completed)
            except Exception as e:
                logger.warning(f"   ⚠️ Failed to fetch {sport_key} on {date_str}: {e}")
        
        return games
    
    def _find_matching_game(self, pred: Prediction, games: List[Dict]) -> Optional[Dict]:
        """
        Find matching game for prediction using string similarity matching.
        Returns the matched game or None.
        """
        if not pred.matchup or not games:
            return None
        
        try:
            # Parse prediction matchup: "Away @ Home"
            parts = pred.matchup.split(' @ ')
            if len(parts) != 2:
                logger.warning(f"   ⚠️ Invalid matchup format: {pred.matchup}")
                return None
            
            pred_away, pred_home = [p.strip() for p in parts]
            
            # Try to find matching game with string similarity
            best_match = None
            best_score = 0.0
            
            for game in games:
                try:
                    # Extract team names from game
                    game_home = game.get('home_team', {}).get('name', '')
                    game_away = game.get('away_team', {}).get('name', '')
                    
                    if not game_home or not game_away:
                        continue
                    
                    # Calculate match score using sequence matching
                    home_match = difflib.SequenceMatcher(None, pred_home.lower(), game_home.lower()).ratio()
                    away_match = difflib.SequenceMatcher(None, pred_away.lower(), game_away.lower()).ratio()
                    total_score = min(home_match, away_match)  # Both must match
                    
                    logger.debug(f"   🔍 Matching {pred_away} @ {pred_home} vs {game_away} @ {game_home}: {total_score:.2f}")
                    
                    if total_score > best_score and total_score >= self.min_match_score:
                        best_score = total_score
                        best_match = game
                
                except Exception as e:
                    logger.debug(f"   ⚠️ Error matching game: {e}")
                    continue
            
            if best_match:
                logger.info(f"   ✅ Found match (score: {best_score:.2f}) for {pred.matchup}")
            
            return best_match
            
        except Exception as e:
            logger.error(f"   ❌ Error in _find_matching_game: {e}")
            return None
    
    async def _resolve_prediction(self, db: AsyncSession, pred: Prediction, game: Dict) -> bool:
        """
        Resolve a single prediction against an actual game result.
        Returns True if successfully resolved and saved.
        """
        try:
            # Extract scores
            home_score = game.get('home_team', {}).get('score', 0)
            away_score = game.get('away_team', {}).get('score', 0)
            
            logger.debug(f"   📊 Game result: {away_score} vs {home_score}")
            
            # Determine if prediction was correct
            result = self._evaluate_prediction(pred, game, home_score, away_score)
            
            if result not in ['win', 'loss', 'push']:
                logger.warning(f"   ⚠️ Could not determine result for {pred.prediction}")
                return False
            
            # Update prediction
            pred.result = result
            pred.resolved_at = datetime.utcnow()
            pred.actual_value = float(home_score + away_score)
            
            db.add(pred)
            await db.commit()
            
            logger.info(f"   ✅ Saved: {pred.matchup} = {result}")
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Failed to save prediction resolution: {e}", exc_info=True)
            await db.rollback()
            return False
    
    def _evaluate_prediction(self, pred: Prediction, game: Dict, home_score: int, away_score: int) -> str:
        """
        Evaluate if prediction was win/loss/push.
        """
        try:
            # Parse prediction text
            pred_text = pred.prediction or ""
            
            logger.debug(f"   🔍 Evaluating prediction: '{pred_text}'")
            
            # Check for moneyline prediction (e.g., "Lakers Win")
            if " Win" in pred_text or " win" in pred_text:
                predicted_team = pred_text.replace(" Win", "").replace(" win", "").strip()
                
                # Find which team was predicted
                game_home = game.get('home_team', {}).get('name', '')
                game_away = game.get('away_team', {}).get('name', '')
                
                # String match to determine which team was predicted
                home_match = difflib.SequenceMatcher(None, predicted_team.lower(), game_home.lower()).ratio()
                away_match = difflib.SequenceMatcher(None, predicted_team.lower(), game_away.lower()).ratio()
                
                if home_match > away_match:
                    # Predicted home
                    return "win" if home_score > away_score else "loss"
                else:
                    # Predicted away
                    return "win" if away_score > home_score else "loss"
            
            # Check for over/under prediction
            elif "Over" in pred_text or "Under" in pred_text:
                parts = pred_text.split()
                if len(parts) >= 2:
                    over_under = parts[0]
                    try:
                        line = float(parts[1].replace(',', ''))
                        total = home_score + away_score
                        
                        if over_under == "Over":
                            return "win" if total > line else ("push" if total == line else "loss")
                        elif over_under == "Under":
                            return "win" if total < line else ("push" if total == line else "loss")
                    except (ValueError, IndexError):
                        logger.warning(f"   ⚠️ Could not parse Over/Under line from: {pred_text}")
            
            logger.warning(f"   ⚠️ Unknown prediction type: {pred_text}")
            return "void"
            
        except Exception as e:
            logger.error(f"   ❌ Error evaluating prediction: {e}")
            return "void"
    
    async def _update_user_stats(self, db: AsyncSession) -> None:
        """Update user win rates based on resolved predictions"""
        from app.models.prediction_records import PredictionRecord
        from sqlalchemy import func, and_, cast, Integer
        
        try:
            # Get all users with resolved predictions
            result = await db.execute(
                select(User.id).distinct().where(
                    User.id.in_(
                        select(PredictionRecord.user_id).where(
                            PredictionRecord.outcome.in_(['hit', 'miss'])
                        )
                    )
                )
            )
            user_ids = result.scalars().all()
            
            logger.info(f"📊 Updating stats for {len(user_ids)} users")
            
            for user_id in user_ids:
                try:
                    # Get user's resolved predictions
                    stats_result = await db.execute(
                        select(
                            func.count(),
                            func.sum(cast(PredictionRecord.outcome == 'hit', Integer()))
                        ).where(
                            and_(
                                PredictionRecord.user_id == user_id,
                                PredictionRecord.outcome.in_(['hit', 'miss'])
                            )
                        )
                    )
                    
                    row = stats_result.first()
                    total = row[0] or 0
                    hits = row[1] or 0
                    
                    # Update user
                    user = await db.get(User, user_id)
                    if user:
                        user.total_predictions = total
                        user.win_rate = (hits / total) if total > 0 else 0.0
                        db.add(user)
                    
                except Exception as e:
                    logger.warning(f"Failed to update stats for user {user_id}: {e}")
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error updating user stats: {e}")
            await db.rollback()
