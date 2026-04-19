from typing import List, Optional, Dict, Any
import logging
from sqlalchemy import select, func, insert, and_
from app.models.db_models import User, user_predictions, Prediction
from datetime import datetime
from app.services.espn_prediction_service import ESPNPredictionService
import asyncio



logger = logging.getLogger(__name__)

class PredictionService:
    """Service for managing predictions"""
    
    # Tier-based daily pick limits - MUST MATCH tier_features.py TierFeatures.TIER_CONFIG
    # These should be consistent with what TierFeatures.get_tier_config() returns
    TIER_LIMITS = {
        'starter': 1,       # Starter tier (free): 1 pick/day
        'basic': 10,        # Basic tier: 10 picks/day
        'pro': 25,          # Pro tier: 25 picks/day
        'pro_plus': 9999,   # Pro Plus tier: unlimited
        'elite': 9999       # Elite tier: unlimited
    }
    
    def __init__(self):
        self.espn_service = ESPNPredictionService()




    async def resolve_predictions(self, db):
        """
        Check unresolved predictions and update their status using ESPN data.
        This is a heavy operation and should be run periodically or via background task.
        """
        from app.models.db_models import Prediction
        from datetime import timedelta
        
        try:
            # 1. Get unresolved predictions that have started
            # Use resolved_at is None
            stmt = select(Prediction).where(
                (Prediction.resolved_at == None) & 
                (Prediction.result == None)
            )
            result = await db.execute(stmt)
            pending_predictions = result.scalars().all()
            
            if not pending_predictions:
                return 0
                
            updated_count = 0
            
            # Group by sport to minimize API calls
            predictions_by_sport = {}
            for p in pending_predictions:
                # We need to map sport_key which isn't directly on the model, 
                # but we might have stored it or can infer it.
                # Actually, Prediction model doesn't have sport_key, it has 'sport' string.
                # But we stored sport_key in the dictionary before saving?
                # Let's check model... 'sport' is "NBA", "NFL".
                # We need to reverse map or store sport_key.
                # For now, let's infer.
                
                sport_key_map = {
                    "NBA": "basketball_nba",
                    "NHL": "icehockey_nhl",
                    "NFL": "americanfootball_nfl",
                    "Soccer": "soccer_epl" # Default to EPL or try MLS if league matches
                }
                
                # Refine mapping based on league if needed
                key = sport_key_map.get(p.sport)
                if p.sport == "Soccer" and "MLS" in (p.league or ""):
                    key = "soccer_usa_mls"
                    
                if key:
                    if key not in predictions_by_sport:
                        predictions_by_sport[key] = []
                    predictions_by_sport[key].append(p)
            
            # 2. Fetch scores for each sport
            # We check Today and Yesterday to cover recent completions
            # and maybe Tomorrow if timezone differences matter
            dates_to_check = [
                datetime.utcnow().strftime("%Y%m%d"),
                (datetime.utcnow() - timedelta(days=1)).strftime("%Y%m%d")
            ]
            
            for sport_key, preds in predictions_by_sport.items():
                all_scores = []
                for date_str in dates_to_check:
                    try:
                        scores = await self.espn_service.get_scoreboard(sport_key, date_str)
                        if scores:
                            all_scores.extend(scores)
                    except Exception as e:
                        logger.error(f"Error fetching scores for {sport_key} on {date_str}: {e}")

                if not all_scores:
                    continue
                    
                # 3. Match and Resolve
                for p in preds:
                    # Match logic: Fuzzy match team names
                    # Prediction has 'matchup' e.g. "Lakers @ Celtics"
                    # We need to parse home/away from matchup string or store them better.
                    # Current matchup string: "Away @ Home"
                    
                    if not p.matchup:
                        continue
                        
                    try:
                        away_name, home_name = p.matchup.split(' @ ')
                    except ValueError:
                        continue
                        
                    # Find game in scores
                    matched_game = None
                    for game in all_scores:
                        # Check if names are contained
                        # ESPN names might be "Los Angeles Lakers" vs "Lakers"
                        # Simple check:
                        h_name_espn = game['home_team']['name']
                        a_name_espn = game['away_team']['name']
                        
                        # Check if our stored name is a substring of ESPN name or vice versa
                        h_match = home_name in h_name_espn or h_name_espn in home_name
                        a_match = away_name in a_name_espn or a_name_espn in away_name
                        
                        if h_match and a_match:
                            matched_game = game
                            break
                    
                    if matched_game and matched_game['completed']:
                        # Determine Result
                        # Parse prediction: "Lakers Win" or "Over 220.5"
                        
                        home_score = matched_game['home_team']['score']
                        away_score = matched_game['away_team']['score']
                        
                        result = None
                        
                        # Moneyline Check
                        if "Win" in p.prediction:
                            predicted_winner = p.prediction.replace(" Win", "")
                            
                            # actual_winner = home_name if home_score > away_score else away_name
                            
                            # Re-verify matching
                            if predicted_winner in matched_game['home_team']['name'] or matched_game['home_team']['name'] in predicted_winner:
                                # Predicted Home
                                result = "win" if home_score > away_score else "loss"
                            elif predicted_winner in matched_game['away_team']['name'] or matched_game['away_team']['name'] in predicted_winner:
                                # Predicted Away
                                result = "win" if away_score > home_score else "loss"
                                
                        # Totals Check (Over/Under)
                        elif "Over" in p.prediction or "Under" in p.prediction:
                            # Parse "Over 220.5"
                            parts = p.prediction.split()
                            if len(parts) >= 2:
                                type_ = parts[0] # Over/Under
                                try:
                                    line = float(parts[1])
                                    total_score = home_score + away_score
                                    
                                    if type_ == "Over":
                                        result = "win" if total_score > line else "loss"
                                    elif type_ == "Under":
                                        result = "win" if total_score < line else "loss"
                                    
                                    if total_score == line:
                                        result = "push"
                                except ValueError:
                                    pass
                                    
                        # Update DB
                        if result:
                            p.result = result
                            p.resolved_at = datetime.utcnow()
                            p.actual_value = float(home_score + away_score) # Store total as value for now
                            updated_count += 1
            
            await db.commit()
            return updated_count
            
        except Exception as e:
            logger.error(f"Error resolving predictions: {e}")
            return 0

    async def get_predictions(
        self,
        db,
        user,
        sport: Optional[str] = None,
        league: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get predictions with filtering and feature gating by user tier using ESPN API only"""
        try:
            # CRITICAL: Extended 180-second timeout to allow full enrichment of predictions
            # Allows ESPN API calls, data enrichment, and model predictions to complete
            # This timeout is necessary for enriching multiple games with stats lookups
            espn_preds = await asyncio.wait_for(
                self._get_predictions_internal(db, user, sport, league, min_confidence, limit, offset),
                timeout=180.0  # Extended timeout: 180s (3 min) for full enrichment of all sports
            )
            return espn_preds
            
        except asyncio.TimeoutError as e:
            logger.error(f"[PREDICTION_SERVICE] Timeout after 180s fetching predictions for {sport}", exc_info=False)
            # Return empty array on timeout - no fake data
            return []
        except Exception as e:
            logger.error(f"[PREDICTION_SERVICE] Error in get_predictions: {str(e)}", exc_info=True)
            # Return empty array on error - no fake data
            return []
    
    async def _get_fallback_predictions_db(self, db, sport: Optional[str], limit: int, offset: int) -> List[Dict[str, Any]]:
        """Fallback to database predictions when ESPN service returns no data"""
        try:
            from app.models.db_models import Prediction
            from sqlalchemy import select
            
            logger.info(f"[PREDICTION_SERVICE] Attempting database fallback for sport={sport}")
            
            # Build query based on sport
            query = select(Prediction)
            
            if sport:
                # Map sport key to sport_key in database
                sport_key = sport
                query = query.where(Prediction.sport_key == sport_key)
            
            # Execute query
            result = await db.execute(query)
            predictions = result.scalars().all()
            
            if predictions:
                logger.info(f"[PREDICTION_SERVICE] Found {len(predictions)} predictions in database for {sport}")
                # Convert to dict format
                preds_list = []
                for pred in predictions:
                    pred_dict = {
                        'id': pred.id,
                        'sport': pred.sport,
                        'league': pred.league,
                        'matchup': pred.matchup,
                        'prediction': pred.prediction,
                        'confidence': float(pred.confidence) if pred.confidence else 50.0,
                        'prediction_type': pred.prediction_type,
                        'sport_key': pred.sport_key,
                        'event_id': pred.event_id,
                        'created_at': pred.created_at.isoformat() if pred.created_at else datetime.utcnow().isoformat(),
                        'game_time': pred.game_time or 'TBD',
                        'odds': pred.odds,
                        'reasoning': pred.reasoning,
                        'models': pred.model_weights
                    }
                    preds_list.append(pred_dict)
                
                # Apply offset and limit
                return preds_list[offset:offset+limit] if offset else preds_list[:limit]
            
            logger.info(f"[PREDICTION_SERVICE] No predictions found in database for {sport}")
            return []
            
        except Exception as e:
            logger.error(f"[PREDICTION_SERVICE] Error querying database fallback: {e}", exc_info=True)
            return []
    
    def _get_fallback_predictions(self, sport: Optional[str], limit: int, offset: int) -> List[Dict[str, Any]]:
        """Return empty list - NO fake data ever. Only real ESPN or Linesmate data."""
        logger.info(f"[PREDICTION_SERVICE] No real predictions available for {sport}. Returning empty array.")
        return []

    async def _get_predictions_internal(
        self,
        db,
        user,
        sport: Optional[str] = None,
        league: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Internal method for getting predictions (wrapped by timeout)"""
        try:
            # Get tier for feature gating
            tier = getattr(user, 'subscription_tier', 'free')
            
            # Feature gating config - Include team stats fields for soccer and other sports
            tier_config = {
                # Include player props fields: player, market_key, point, season_avg, recent_10_avg
                # Include team props fields: home_gpg, away_gpg, home_ga, away_ga, home_ppg, away_ppg, etc
                # Include all stat fields that props might contain
                'free': {'fields': ['id','sport_key','event_id','sport','league','matchup','game_time','game_time_status','prediction','confidence','prediction_type','created_at','player','market_key','point','season_avg','recent_10_avg','market_name','team_name','odds','reasoning','models',
                                    'home_gpg','away_gpg','home_ga','away_ga','home_ppg','away_ppg','home_oppg','away_oppg','home_rpg','away_rpg','home_ra','away_ra','expected_value','has_espn_stats','is_locked','is_club_100_pick','anytime_goal_names']},
                'starter': {'fields': ['id','sport_key','event_id','sport','league','matchup','game_time','game_time_status','prediction','confidence','prediction_type','created_at','player','market_key','point','season_avg','recent_10_avg','market_name','team_name','odds','reasoning','models',
                                       'home_gpg','away_gpg','home_ga','away_ga','home_ppg','away_ppg','home_oppg','away_oppg','home_rpg','away_rpg','home_ra','away_ra','expected_value','has_espn_stats','is_locked','is_club_100_pick','anytime_goal_names']},
                'basic': {'fields': ['id','sport_key','event_id','sport','league','matchup','game_time','game_time_status','prediction','confidence','odds','prediction_type','reasoning','created_at','player','market_key','point','season_avg','recent_10_avg','market_name','team_name','models',
                                     'home_gpg','away_gpg','home_ga','away_ga','home_ppg','away_ppg','home_oppg','away_oppg','home_rpg','away_rpg','home_ra','away_ra','expected_value','has_espn_stats','is_locked','is_club_100_pick','anytime_goal_names']},
                'pro': {'fields': ['id','sport_key','event_id','sport','league','matchup','game_time','game_time_status','prediction','confidence','odds','prediction_type','reasoning','models','created_at','resolved_at','result','player','market_key','point','season_avg','recent_10_avg','market_name','team_name',
                                   'home_gpg','away_gpg','home_ga','away_ga','home_ppg','away_ppg','home_oppg','away_oppg','home_rpg','away_rpg','home_ra','away_ra','expected_value','has_espn_stats','is_locked','is_club_100_pick','anytime_goal_names']},
                'elite': {'fields': ['id','sport_key','event_id','sport','league','matchup','game_time','game_time_status','prediction','confidence','odds','prediction_type','reasoning','models','created_at','resolved_at','result','player','market_key','point','season_avg','recent_10_avg','market_name','team_name',
                                     'home_gpg','away_gpg','home_ga','away_ga','home_ppg','away_ppg','home_oppg','away_oppg','home_rpg','away_rpg','home_ra','away_ra','expected_value','has_espn_stats','is_locked','is_club_100_pick','anytime_goal_names']},
            }

            config = tier_config.get(tier, tier_config['free'])

            all_predictions = []
            
            # Handle comma-separated sport keys (e.g., "soccer_epl,soccer_usa_mls")
            if sport and ',' in sport:
                sports_list = [s.strip() for s in sport.split(',')]
                logger.info(f"[PREDICTION_SERVICE] Handling comma-separated sports: {sports_list}")
                
                # Fetch predictions for each sport individually
                for single_sport in sports_list:
                    try:
                        espn_preds = await self.espn_service.get_predictions(
                            sport=single_sport,
                            league=league,
                            min_confidence=min_confidence,
                            limit=limit  # Fetch limit per sport
                        )
                        all_predictions.extend(espn_preds)
                    except Exception as e:
                        logger.warning(f"[PREDICTION_SERVICE] Error fetching predictions for {single_sport}: {e}")
                        continue
            else:
                # Single sport - use existing behavior
                all_predictions = await self.espn_service.get_predictions(
                    sport=sport,
                    league=league,
                    min_confidence=min_confidence,
                    limit=limit + offset  # Fetch enough to handle offset
                )
                logger.info(f"[PREDICTION_SERVICE] ESPNPredictionService returned {len(all_predictions)} predictions for sport={sport}")
            
            logger.info(f"[PREDICTION_SERVICE] After initial fetch: {len(all_predictions)} predictions")

            # If no predictions found, try database fallback before giving up
            if not all_predictions:
                logger.warning("[PREDICTION_SERVICE] No predictions from ESPN; trying database fallback")
                db_predictions = await self._get_fallback_predictions_db(db, sport, limit, offset)
                if db_predictions:
                    logger.info(f"[PREDICTION_SERVICE] Using {len(db_predictions)} predictions from database fallback")
                    all_predictions = db_predictions
                else:
                    logger.warning("[PREDICTION_SERVICE] Database fallback also returned no predictions; trying explicit sequential fallback sports")
                    fallback_sports = [
                        'basketball_nba', 'americanfootball_nfl', 'baseball_mlb',
                        'icehockey_nhl', 'soccer_epl', 'soccer_usa_mls',
                    ]
                    for fallback_sport in fallback_sports:
                        try:
                            fallback_pred = await self.espn_service.get_predictions(
                                sport=fallback_sport,
                                league=league,
                                min_confidence=min_confidence,
                                limit=limit + offset
                            )
                            if fallback_pred:
                                all_predictions.extend(fallback_pred)
                                if len(all_predictions) >= limit + offset:
                                    break
                        except Exception as e:
                            logger.warning(f"[PREDICTION_SERVICE] Fallback sport {fallback_sport} failed: {e}")
            # If still no predictions, try database fallback for all sports
            elif not all_predictions:
                logger.warning("[PREDICTION_SERVICE] Fallback sports also returned no predictions; trying database")
                db_predictions = await self._get_fallback_predictions_db(db, None, limit, offset)
                if db_predictions:
                    all_predictions = db_predictions

            # Apply tier-based field filtering
            filtered_predictions = []
            for pred in all_predictions:
                # Apply tier-based field filtering
                filtered_pred = {k: v for k, v in pred.items() if k in config['fields']}
                filtered_predictions.append(filtered_pred)
            
            logger.warning(f"[DEBUG] PredictionService: Received {len(all_predictions)} predictions from ESPN service")
            logger.warning(f"[DEBUG] PredictionService: After tier filtering ({tier}): {len(filtered_predictions)} predictions")
            if filtered_predictions:
                logger.warning(f"[DEBUG] PredictionService: First filtered prediction: {filtered_predictions[0]}")
            
            # Filter out games that have already started or been completed
            # Only show games that haven't started yet
            from datetime import datetime as dt_class
            future_predictions = []
            today = dt_class.now()
            
            for pred in filtered_predictions:
                # Skip games that are already completed/live
                game_time_status = pred.get('game_time_status', '').lower()
                game_time_str = pred.get('game_time', '').lower()
                
                # 1. Filter out games with FINAL, LIVE, COMPLETED, POSTPONED, CANCELLED statuses
                if game_time_status in ['final', 'live', 'completed', 'postponed', 'cancelled']:
                    logger.info(f"[FILTER] Skipping game {pred.get('id')} - status: {game_time_status}")
                    continue
                
                # 2. Filter out games where game_time shows "completed", "live", or "final"
                if any(x in game_time_str for x in ['completed', 'live', 'final']):
                    logger.info(f"[FILTER] Skipping game {pred.get('id')} due to game_time: {game_time_str}")
                    continue
                
                # 3. FILTER OUT TBD GAMES - No time/date specified
                if game_time_status == 'tbd' or 'tbd' in game_time_str:
                    logger.info(f"[FILTER] Skipping game {pred.get('id')} - TBD time not set: {game_time_str}")
                    continue
                
                # 4. REJECT ANY games where game_time is missing/empty/null
                if not game_time_str or game_time_str.strip() in ['', 'time tbd', 'none']:
                    logger.info(f"[FILTER] Skipping game {pred.get('id')} - no valid game time: {game_time_str}")
                    continue
                
                # 5. FILTER BY DATE - Only show games from today onwards
                # Extract date from game_time (format: "Jan 15, 7:00 PM ET" or similar)
                # If we can parse it, verify it's not from a past date
                try:
                    # Try to extract the date parts from game_time_str
                    # Format example: "apr 03, 7:00 pm et" -> check if it's from today/future
                    if game_time_str and ',' in game_time_str:
                        # Parse "Apr 03" part
                        date_part = game_time_str.split(',')[0].strip()
                        try:
                            # Try parsing as "Apr 03" format for current year
                            game_date = dt_class.strptime(f"{date_part} {today.year}", "%b %d %Y")
                            
                            # If the parsed date is before today's date at start of day, skip it
                            today_start = dt_class(today.year, today.month, today.day)
                            if game_date < today_start:
                                logger.info(f"[FILTER] Skipping game {pred.get('id')} - date is in the past: {game_time_str}")
                                continue
                        except Exception as e:
                            logger.debug(f"[FILTER] Could not parse game date {date_part}: {e}")
                            # If we can't parse, don't filter it
                except Exception as e:
                    logger.debug(f"[FILTER] Error checking game date: {e}")
                
                future_predictions.append(pred)
            
            logger.info(f"[FILTER] After filtering past games/TBD: {len(future_predictions)} predictions (filtered out {len(filtered_predictions) - len(future_predictions)})")
            filtered_predictions = future_predictions
            
            # Apply offset
            if offset > 0:
                filtered_predictions = filtered_predictions[offset:]
            
            # Apply final limit
            if limit > 0 and len(filtered_predictions) > limit:
                filtered_predictions = filtered_predictions[:limit]
            
            return filtered_predictions

        except asyncio.TimeoutError as e:
            logger.error(f"Timeout in get_predictions: {str(e)}", exc_info=True)
            raise TimeoutError(f"Failed to fetch predictions within timeout: {str(e)}") from e
        except Exception as e:
            logger.error(f"Error in get_predictions: {str(e)}", exc_info=True)
            raise




    async def get_prediction_by_id(self, db, prediction_id: str):
        """Get single prediction"""
        # Since we don't store predictions in DB yet, we can't easily retrieve by ID
        # without re-fetching everything. 
        # For now, return None as we are strictly avoiding mock data.
        return None

    def _derive_sport_and_league(self, prediction_data: Dict[str, Any]) -> tuple:
        """Derive sport and league from sport_key or direct fields"""
        # First check if sport and league are directly provided
        if prediction_data.get('sport') and prediction_data.get('league'):
            return prediction_data.get('sport'), prediction_data.get('league')
        
        # Try to derive from sport_key
        sport_key = prediction_data.get('sport_key', '').lower()
        
        # Mapping from sport_key to (sport, league)
        if 'basketball_nba' in sport_key:
            return 'basketball', 'nba'
        elif 'basketball_ncaa' in sport_key:
            return 'basketball', 'ncaa'
        elif 'basketball' in sport_key:
            return 'basketball', sport_key.split('_')[1] if '_' in sport_key else 'unknown'
        elif 'football_nfl' in sport_key:
            return 'football', 'nfl'
        elif 'football_nfl_draft' in sport_key:
            return 'football', 'nfl_draft'
        elif 'football_ncaa' in sport_key:
            return 'football', 'ncaa'
        elif 'football' in sport_key:
            return 'football', sport_key.split('_')[1] if '_' in sport_key else 'unknown'
        elif 'baseball_mlb' in sport_key:
            return 'baseball', 'mlb'
        elif 'baseball' in sport_key:
            return 'baseball', sport_key.split('_')[1] if '_' in sport_key else 'unknown'
        elif 'hockey_nhl' in sport_key:
            return 'hockey', 'nhl'
        elif 'hockey' in sport_key:
            return 'hockey', sport_key.split('_')[1] if '_' in sport_key else 'unknown'
        elif 'soccer' in sport_key:
            # Soccer format: soccer_country_league (e.g., soccer_usa_mls, soccer_epl)
            parts = sport_key.split('_')
            league = parts[-1] if len(parts) > 1 else 'unknown'
            return 'soccer', league
        else:
            # Unknown sport_key, use a safe default
            return 'unknown', 'unknown'

    async def save_prediction(self, db, prediction_data: Dict[str, Any], is_club_100_pick: bool = False):
        """Save prediction to database if it doesn't exist"""
        from app.models.db_models import Prediction
        try:
            prediction_id = prediction_data.get('id')
            logger.info(f"[SAVE_PREDICTION] Attempting to save prediction {prediction_id}")
            logger.debug(f"[SAVE_PREDICTION] Received data keys: {list(prediction_data.keys())}")
            
            # Check if exists
            stmt = select(Prediction).where(Prediction.id == prediction_id)
            result = await db.execute(stmt)
            if result.first():
                logger.info(f"[SAVE_PREDICTION] Prediction {prediction_id} already exists, skipping save")
                return
            
            # Derive sport and league from sport_key if not provided
            sport, league = self._derive_sport_and_league(prediction_data)
            logger.info(f"[SAVE_PREDICTION] Derived sport={sport}, league={league} from sport_key={prediction_data.get('sport_key')}")
            
            # Provide safe defaults for required fields
            matchup = prediction_data.get('matchup') or 'Unknown Matchup'
            prediction = prediction_data.get('prediction') or 'Prediction'
            confidence = prediction_data.get('confidence')
            if confidence is None:
                confidence = 50.0  # Default 50% confidence
            else:
                try:
                    confidence = float(confidence)
                except (ValueError, TypeError):
                    confidence = 50.0
            
            prediction_type = prediction_data.get('prediction_type') or 'unknown'
            
            # Optional fields with safe defaults
            odds = prediction_data.get('odds')
            player = prediction_data.get('player')
            market_key = prediction_data.get('market_key')
            point = prediction_data.get('point')
            event_id = prediction_data.get('event_id')
            sport_key = prediction_data.get('sport_key')
            game_time = prediction_data.get('game_time')
            reasoning = prediction_data.get('reasoning') or []
            model_weights = prediction_data.get('models') or {}
            
            logger.info(f"[SAVE_PREDICTION] Creating prediction with: matchup={matchup}, prediction={prediction}, confidence={confidence}, type={prediction_type}")
            
            try:
                new_pred = Prediction(
                    id=prediction_id,
                    sport=sport,
                    league=league,
                    matchup=matchup,
                    prediction=prediction,
                    confidence=confidence,
                    odds=odds,
                    prediction_type=prediction_type,
                    # Player props specific fields
                    player=player,
                    market_key=market_key,
                    point=point,
                    # Game/Event info
                    event_id=event_id,
                    sport_key=sport_key,
                    game_time=game_time,
                    # Reasoning and models
                    reasoning=reasoning,
                    model_weights=model_weights,
                    # Club 100 tracking
                    is_club_100_pick=is_club_100_pick,
                    created_at=datetime.utcnow()
                )
                
                db.add(new_pred)
                await db.commit()
                logger.info(f"[SAVE_PREDICTION] ✅ Successfully saved prediction {prediction_id} with sport={sport}, league={league}")
                return True  # Indicate success
            except Exception as insert_err:
                logger.error(f"[SAVE_PREDICTION] ❌ Error during insert/commit: {type(insert_err).__name__}: {str(insert_err)}", exc_info=True)
                try:
                    await db.rollback()
                except:
                    pass
                raise ValueError(f"Database insert failed: {str(insert_err)}")
            
        except Exception as e:
            logger.error(f"[SAVE_PREDICTION] ❌ Error saving prediction {prediction_data.get('id', 'UNKNOWN')}: {e}", exc_info=True)
            try:
                await db.rollback()
            except:
                pass
            # CRITICAL: Re-raise the exception so follow_prediction knows if save failed
            # Otherwise, the insert into user_predictions will fail with a foreign key constraint violation
            raise ValueError(f"Failed to save prediction to database: {str(e)}")

    async def follow_prediction(self, db, user_id: str, prediction_data: Dict[str, Any], is_club_100_pick: bool = False):
        """Follow a prediction with strict daily limit enforcement"""
        try:
            prediction_id = prediction_data.get('id')
            if not prediction_id:
                raise ValueError("Prediction ID required")
            
            logger.info(f"[FOLLOW_SERVICE] Starting follow - user_id={user_id}, prediction_id={prediction_id}, is_club_100_pick={is_club_100_pick}, type={type(prediction_id)}")

            # 1. Get user tier and limits
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise ValueError("User not found")
                
            tier = (user.subscription_tier or 'starter').lower().strip()
            
            # Get tier-based daily limit
            max_picks = self.TIER_LIMITS.get(tier, 1)

            
            # 2. Check if already followed
            stmt = select(user_predictions).where(
                (user_predictions.c.user_id == user_id) & 
                (user_predictions.c.prediction_id == prediction_id)
            )
            result = await db.execute(stmt)
            if result.first():
                logger.info(f"[FOLLOW_SERVICE] Already following {prediction_id}")
                return True # Already following
                
            # 3. Count today's picks (excluding club_100_access picks which are just for access cost)
            from datetime import timezone
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
            count_stmt = select(func.count()).select_from(user_predictions).join(
                Prediction, user_predictions.c.prediction_id == Prediction.id
            ).where(
                and_(
                    user_predictions.c.user_id == user_id,
                    user_predictions.c.created_at >= today_start,
                    Prediction.sport != 'club_100_access'  # Don't count access cost picks
                )
            )
            count_result = await db.execute(count_stmt)
            current_picks = count_result.scalar() or 0
            
            logger.info(f"[FOLLOW_SERVICE] Current picks today: {current_picks}/{max_picks}, is_club_100_pick={is_club_100_pick}")
            
            if current_picks >= max_picks:
                # If they try to bypass, we block them
                error_msg = f"Daily pick limit reached. You have used {current_picks} of {max_picks} picks today. Upgrade your plan for more picks!"
                logger.warning(f"[FOLLOW_SERVICE] ❌ {error_msg} User: {user_id} ({tier})")
                raise ValueError(error_msg)
            
            # 4. Save prediction to DB first (upsert) - include is_club_100_pick flag
            try:
                await self.save_prediction(db, prediction_data, is_club_100_pick=is_club_100_pick)
                logger.info(f"[FOLLOW_SERVICE] Saved prediction {prediction_id} to DB with is_club_100_pick={is_club_100_pick}")
            except ValueError as save_err:
                logger.error(f"[FOLLOW_SERVICE] ❌ Failed to save prediction: {str(save_err)}")
                raise ValueError(f"Could not save prediction: {str(save_err)}")
            except Exception as save_err:
                logger.error(f"[FOLLOW_SERVICE] ❌ Unexpected error saving prediction: {str(save_err)}", exc_info=True)
                raise ValueError(f"Database error saving prediction: {str(save_err)}")

            # 5. Record prediction in user's prediction history for accuracy tracking
            # This is CRITICAL for the accuracy dashboard to work!
            try:
                from app.services.prediction_history_service import PredictionHistoryService
                history_service = PredictionHistoryService(db)
                await history_service.record_prediction(
                    user_id=user_id,
                    sport_key=prediction_data.get('sport_key'),
                    event_id=prediction_data.get('event_id'),
                    prediction_data=prediction_data
                )
                logger.info(f"[FOLLOW_SERVICE] Recorded prediction in PredictionRecord for tracking")
            except Exception as history_err:
                logger.warning(f"[FOLLOW_SERVICE] Warning: Failed to record prediction history: {history_err}")
                # Don't fail the whole follow if history recording fails
                pass

            # 6. Insert new pick
            from datetime import timezone
            ins_stmt = insert(user_predictions).values(
                user_id=user_id,
                prediction_id=prediction_id,
                created_at=datetime.now(timezone.utc)
            )
            await db.execute(ins_stmt)
            logger.info(f"[FOLLOW_SERVICE] Inserted into user_predictions: user_id={user_id}, prediction_id={prediction_id}")
            
            await db.commit()
            logger.info(f"[FOLLOW_SERVICE] ✅ Committed to database - user_id={user_id}, prediction_id={prediction_id}, is_club_100_pick={is_club_100_pick}")
            
            return True
        except ValueError as e:
            raise e
        except Exception as e:
            logger.error(f"[FOLLOW_SERVICE] ❌ Unexpected error following prediction {prediction_data.get('id', 'UNKNOWN')}: {str(e)}", exc_info=True)
            # Provide specific error details
            error_msg = str(e)
            if 'UNIQUE constraint failed' in error_msg:
                raise ValueError("This prediction is already in your list")
            elif 'FOREIGN KEY constraint failed' in error_msg:
                raise ValueError("The prediction data is invalid or incomplete")
            elif 'no such table' in error_msg.lower():
                raise ValueError("Database initialization incomplete")
            else:
                raise ValueError(f"Database error: {error_msg}")

    async def unfollow_prediction(self, db, user_id: str, prediction_id: str):
        """Unfollow a prediction"""
        return True

    async def get_daily_picks_count(self, db, user_id: str) -> int:
        """Get the number of picks the user has made today (excludes Club 100 access cost picks)"""
        try:
            # Use timezone-aware UTC datetime to ensure proper comparison with database timestamps
            from datetime import timezone
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Count picks excluding club_100_access (which are just for access cost, not actual predictions)
            count_stmt = select(func.count()).select_from(user_predictions).join(
                Prediction, user_predictions.c.prediction_id == Prediction.id
            ).where(
                and_(
                    user_predictions.c.user_id == user_id,
                    user_predictions.c.created_at >= today_start,
                    Prediction.sport != 'club_100_access'  # Don't count access cost picks
                )
            )
            count_result = await db.execute(count_stmt)
            result = count_result.scalar() or 0
            logger.debug(f"[DAILY_PICKS_COUNT] user_id={user_id}, today_start={today_start}, count={result}")
            return result
        except Exception as e:
            logger.error(f"Error getting daily picks count: {e}", exc_info=True)
            return 0

    async def is_following_prediction(self, db, user_id: str, prediction_id: str) -> bool:
        """Check if user is already following a prediction"""
        try:
            stmt = select(user_predictions).where(
                (user_predictions.c.user_id == user_id) & 
                (user_predictions.c.prediction_id == prediction_id)
            )
            result = await db.execute(stmt)
            is_following = result.first() is not None
            logger.debug(f"[IS_FOLLOWING] user_id={user_id}, prediction_id={prediction_id}, is_following={is_following}")
            return is_following
        except Exception as e:
            logger.error(f"Error checking if following prediction (user_id={user_id}, pred_id={prediction_id}): {e}", exc_info=True)
            return False


    def _convert_odds_to_decimal(self, odds_str: Optional[str]) -> float:
        """Convert American odds string to decimal multiplier"""
        try:
            if not odds_str:
                return 1.91 # Default standard -110 roughly
            
            val = float(odds_str)
            if val > 0:
                return (val / 100) + 1
            elif val < 0:
                return (100 / abs(val)) + 1
            else:
                return 1.0
        except (ValueError, TypeError):
            return 1.91

    async def get_user_stats(self, db, user_id: str):
        """Get user statistics based on resolved predictions"""
        from app.models.db_models import Prediction
        
        try:
            # Join user_predictions with predictions to get results
            stmt = select(Prediction).join(
                user_predictions, 
                user_predictions.c.prediction_id == Prediction.id
            ).where(
                user_predictions.c.user_id == user_id
            )
            
            result = await db.execute(stmt)
            predictions = result.scalars().all()
            
            total = len(predictions)
            wins = 0
            losses = 0
            pushes = 0
            profit_loss = 0.0
            total_wagered = 0.0 # Assuming 1 unit per bet
            
            for p in predictions:
                if p.result == 'win':
                    wins += 1
                    decimal_odds = self._convert_odds_to_decimal(p.odds)
                    # Profit = (Stake * Decimal) - Stake = Stake * (Decimal - 1)
                    profit = 1.0 * (decimal_odds - 1)
                    profit_loss += profit
                    total_wagered += 1.0
                elif p.result == 'loss':
                    losses += 1
                    profit_loss -= 1.0
                    total_wagered += 1.0
                elif p.result == 'push':
                    pushes += 1
                    total_wagered += 1.0 # Push returns stake, no profit/loss
                
                # If pending (result is None), we don't count towards W/L or Profit yet
                # but maybe count towards "pending" stats if needed.
            
            win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0.0
            roi = (profit_loss / total_wagered) * 100 if total_wagered > 0 else 0.0
            
            return {
                "win_rate": round(win_rate, 1),
                "total_predictions": total,
                "profit_loss": round(profit_loss, 2), # In units
                "roi": round(roi, 1),
                "wins": wins,
                "losses": losses,
                "pending": total - (wins + losses + pushes)
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {
                "win_rate": 0,
                "total_predictions": 0,
                "profit_loss": 0,
                "roi": 0,
                "wins": 0,
                "losses": 0,
                "pending": 0
            }
