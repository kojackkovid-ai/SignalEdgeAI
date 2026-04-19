from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Header, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, insert
from app.database import get_db
from app.services.auth_service import AuthService
from app.services.prediction_service import PredictionService
from app.services.espn_prediction_service import ESPNPredictionService
from app.services.data_validation_service import get_data_validation_service
from app.models.tier_features import TierFeatures
from app.models.db_models import user_predictions, User
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import asyncio

router = APIRouter()

logger = logging.getLogger(__name__)

# Singleton instances - created once and reused across all requests
_auth_service_instance = None
_prediction_service_instance = None
_espn_service_instance = None

# Dependency functions for service injection
def get_auth_service() -> AuthService:
    """Get or create AuthService instance (singleton)"""
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = AuthService()
    return _auth_service_instance

def get_prediction_service() -> PredictionService:
    """Get or create PredictionService instance (singleton)"""
    global _prediction_service_instance
    if _prediction_service_instance is None:
        _prediction_service_instance = PredictionService()
    return _prediction_service_instance

def get_espn_service() -> ESPNPredictionService:
    """Get or create ESPNPredictionService instance (singleton)"""
    global _espn_service_instance
    if _espn_service_instance is None:
        _espn_service_instance = ESPNPredictionService()
    return _espn_service_instance

async def get_current_user_optional(authorization: Optional[str] = Header(None, description="Bearer token")) -> Optional[str]:
    """Extract user ID from Bearer token - optional, returns None if not provided"""
    if authorization is None:
        return None
    
    auth_service = AuthService()
    try:
        # Extract token from "Bearer <token>"
        parts = authorization.split()
        if len(parts) != 2:
            return None
        
        scheme, token = parts
        if scheme.lower() != "bearer":
            return None
        
        user_id = auth_service._decode_token(token)
        return user_id
        
    except Exception as e:
        logger.debug(f"[Auth] Optional auth failed: {str(e)}")
        return None

async def get_current_user(authorization: Optional[str] = Header(None, description="Bearer token")) -> str:
    """Extract user ID from Bearer token in Authorization header - REQUIRED"""
    logger.info(f"[Auth] Authorization header present: {bool(authorization)}")
    logger.debug(f"[Auth] Authorization header value: {authorization[:20] if authorization else 'None'}...")
    
    if authorization is None:
        logger.warning("[Auth] Missing authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    auth_service = AuthService()
    try:
        # Extract token from "Bearer <token>"
        parts = authorization.split()
        if len(parts) != 2:
            logger.warning(f"[Auth] Invalid authorization format: expected 2 parts, got {len(parts)}")
            raise ValueError("Invalid format")
        
        scheme, token = parts
        if scheme.lower() != "bearer":
            logger.warning(f"[Auth] Invalid authentication scheme: {scheme}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
        
        user_id = auth_service._decode_token(token)
        logger.info(f"[Auth] Successfully decoded token for user: {user_id}")
        return user_id
        
    except ValueError as e:
        logger.warning(f"[Auth] Token decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    except Exception as e:
        logger.error(f"[Auth] Unexpected error decoding token: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

class ReasoningPoint(BaseModel):
    factor: str
    impact: str
    weight: float
    explanation: str

class ModelEnsemble(BaseModel):
    name: str
    prediction: str
    confidence: float
    weight: float

class PredictionResponse(BaseModel):
    id: str
    sport: Optional[str] = None
    league: Optional[str] = None
    matchup: str
    game_time: Optional[str] = None
    prediction: str
    confidence: float
    prediction_type: str
    created_at: str
    odds: Optional[str] = None
    reasoning: Optional[List[ReasoningPoint]] = None
    models: Optional[List[ModelEnsemble]] = None
    resolved_at: Optional[str] = None
    result: Optional[str] = None
    player: Optional[str] = None
    market_key: Optional[str] = None
    market_name: Optional[str] = None  # Add stat category name
    point: Optional[float] = None
    sport_key: Optional[str] = None
    event_id: Optional[str] = None
    is_locked: Optional[bool] = True
    daily_picks_used: Optional[int] = None
    daily_picks_limit: Optional[int] = None
    team_name: Optional[str] = None  # Add team name
    season_avg: Optional[float] = None  # Add season average stat
    recent_10_avg: Optional[float] = None  # Add recent 10 games average

class GetPredictionsQuery(BaseModel):
    sport: Optional[str] = None
    league: Optional[str] = None
    min_confidence: float = 0.0
    limit: int = 10
    offset: int = 0

class PredictionsListResponse(BaseModel):
    predictions: List[PredictionResponse]

# Helper function to get tier features from centralized config
def get_tier_features(tier: str) -> Dict[str, Any]:
    """Get tier features from TierFeatures configuration"""
    config = TierFeatures.get_tier_config(tier)
    if not config:
        # Fallback to starter tier if config not found
        config = TierFeatures.get_tier_config('starter') or {}
    
    # Convert tier config to the format expected by existing code
    return {
        'show_odds': config.get('show_odds', False),
        'show_reasoning': config.get('show_reasoning', False),
        'show_models': config.get('show_models', False),
        'show_line': config.get('show_line', False),
        'show_full_reasoning': config.get('show_full_reasoning', False),
        'show_advanced_analysis': config.get('show_advanced_analysis', False),
        'show_detailed_models': config.get('show_detailed_models', False),
        'reasoning_count': config.get('reasoning_count', 0),
        'models_count': config.get('models_count', 0),
        'dailyLimit': config.get('predictions_per_day') or 999999
    }

def is_player_prop_id(prediction_id: str) -> bool:
    """
    Determine if a prediction ID represents a player prop.
    Player prop IDs have format: {event_id}_{market_key}_{player_name}
    where market_key can be single or multi-word (e.g., 'points', 'home_runs', 'pass_yards')
    """
    if not prediction_id or '_' not in prediction_id:
        return False
    
    parts = prediction_id.split('_')
    # Need at least 3 parts: event_id, market_key, player_name
    if len(parts) < 3:
        return False
    
    # Common player prop market keys (single and multi-word)
    player_prop_markets = {
        # Single word markets
        'points', 'rebounds', 'assists', 'goals', 'saves', 'hits', 'rbi', 'hr',
        # Multi-word markets (underscore separated)
        'home_runs', 'pass_yards', 'rush_yards', 'rec_yards', 'passing_yards', 
        'rushing_yards', 'receiving_yards', 'three_pointers', 'steals', 'blocks',
        'shots', 'sog', 'faceoff_wins',
        # MLB markets
        'runs_batted_in', 'stolen_bases', 'batting_average'
    }
    
    # The market key is everything between event_id and player_name
    # ID format: {event_id}_{market_key}_{player_name}
    # e.g., "401672633_home_runs_Aaron_Judge" -> market_key = "home_runs"
    # e.g., "401672633_points_LeBron_James" -> market_key = "points"
    
    # Try to identify market key by checking all possible positions
    # Start from position 1 (after event_id) and try different lengths
    for i in range(1, len(parts) - 1):  # At least 1 part for player name at the end
        potential_market = '_'.join(parts[1:i+1]).lower()
        if potential_market in player_prop_markets:
            return True
    
    # Also check if any part matches a single-word market
    for part in parts[1:-1]:  # Skip first (event_id) and last (player_name)
        if part.lower() in player_prop_markets:
            return True
    
    return False

def parse_player_prop_id(prediction_id: str) -> Dict[str, str]:
    """
    Parse a player prop ID and extract event_id, market_key, and player_name.
    ID format: {event_id}_{market_key}_{player_name}
    e.g., "401866758_rebounds_Paolo_Banchero"
    Returns: {"event_id": "401866758", "market_key": "rebounds", "player_name": "Paolo Banchero"}
    """
    if not prediction_id or '_' not in prediction_id:
        return {}
    
    parts = prediction_id.split('_')
    if len(parts) < 3:
        return {}
    
    player_prop_markets = {
        # Single word markets
        'points', 'rebounds', 'assists', 'goals', 'saves', 'hits', 'rbi', 'hr',
        # Multi-word markets (underscore separated)
        'home_runs', 'pass_yards', 'rush_yards', 'rec_yards', 'passing_yards', 
        'rushing_yards', 'receiving_yards', 'three_pointers', 'steals', 'blocks',
        'shots', 'sog', 'faceoff_wins',
        # MLB markets
        'runs_batted_in', 'stolen_bases', 'batting_average'
    }
    
    # Find the market key
    market_end_idx = None
    for i in range(1, len(parts) - 1):
        potential_market = '_'.join(parts[1:i+1]).lower()
        if potential_market in player_prop_markets:
            market_end_idx = i
            break
    
    if market_end_idx is None:
        # Single-word market
        for i, part in enumerate(parts[1:-1], 1):
            if part.lower() in player_prop_markets:
                market_end_idx = i
                break
    
    if market_end_idx is None:
        return {}
    
    event_id = parts[0]
    market_key = '_'.join(parts[1:market_end_idx+1])
    player_name = '_'.join(parts[market_end_idx+1:])
    
    return {
        "event_id": event_id,
        "market_key": market_key,
        "player_name": player_name.replace('_', ' ')  # Convert underscores to spaces
    }

# REMOVED: No fallback mock data ever - only real ESPN data
# If ESPN service fails or returns no data, return empty list only

@router.get("/props/{sport_key}/{event_id}", response_model=List[PredictionResponse])
async def get_event_props(
    sport_key: str,
    event_id: str,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get player props for a specific event with validation and tier filtering"""
    request_id = f"{sport_key}_{event_id}_{datetime.utcnow().timestamp()}"
    logger.info(f"[{request_id}] Getting player props for {sport_key}/{event_id} - User: {current_user_id}")
    
    try:
        # Get data validation service
        validator = get_data_validation_service()
        
        # Get user's tier and daily picks info
        try:
            result = await db.execute(select(User).where(User.id == current_user_id))
            user = result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[{request_id}] Database error fetching user: {e}")
            user = None
        
        normalized_tier = 'starter'
        if user:
            normalized_tier = (user.subscription_tier or 'starter').lower().strip()
            logger.info(f"[{request_id}] User tier: {normalized_tier}")
        else:
            logger.warning(f"[{request_id}] User not found, using default tier")
        
        try:
            tier_config = TierFeatures.get_tier_config(normalized_tier)
            daily_limit = tier_config.get('predictions_per_day') or 999999
            daily_picks_used = await get_prediction_service().get_daily_picks_count(db, current_user_id)
            logger.info(f"[{request_id}] Daily picks: {daily_picks_used}/{daily_limit}")
        except Exception as e:
            logger.error(f"[{request_id}] Error getting daily picks count: {e}")
            daily_limit = 1
            daily_picks_used = 0
        
        # Get tier features
        tier_features = get_tier_features(normalized_tier)
        
        # Try ESPN service first
        logger.info(f"[{request_id}] Calling ESPN service for player props")
        try:
            props = await get_espn_service().get_player_props(sport_key, event_id)
            logger.info(f"[{request_id}] ESPN service returned {len(props)} props")
        except asyncio.TimeoutError:
            logger.error(f"[{request_id}] Timeout calling ESPN service for {sport_key}/{event_id}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Request timed out while fetching player props from ESPN"
            )
        except Exception as e:
            logger.error(f"[{request_id}] Error calling ESPN service: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch player props from ESPN: {str(e)}"
            )
        
        if props:
            # Validate each prop before returning
            validated_props = []
            validation_issues = 0
            
            for prop in props:
                try:
                    # Validate game data structure
                    is_valid, errors = validator.validate_game_data(prop, sport_key)
                    
                    if not is_valid:
                        logger.warning(f"[{request_id}] Prop {prop.get('id', 'unknown')} failed validation: {errors}")
                        validation_issues += 1
                        continue  # Skip invalid props
                    
                    # Add daily picks info and check following status for each prop
                    prop['daily_picks_used'] = daily_picks_used
                    prop['daily_picks_limit'] = daily_limit
                    
                    # Check if user is already following this prediction
                    prop_id = prop.get('id', '')
                    if prop_id:
                        try:
                            is_following = await get_prediction_service().is_following_prediction(db, current_user_id, prop_id)
                            prop['is_locked'] = not is_following
                        except Exception as e:
                            logger.warning(f"[{request_id}] Error checking follow status for {prop_id}: {e}")
                            prop['is_locked'] = True
                    
                    # For Pro/Pro Plus/Elite users, always show models
                    # For lower tiers, only show models if already following (unlocked)
                    show_all = normalized_tier in ['pro', 'pro_plus', 'elite'] or not prop.get('is_locked', True)
                    
                    if not show_all:
                        if not tier_features['show_odds']:
                            prop['odds'] = None
                        if not tier_features['show_reasoning']:
                            prop['reasoning'] = None
                        if not tier_features['show_models']:
                            prop['models'] = None
                    
                    validated_props.append(prop)
                    
                except Exception as e:
                    logger.warning(f"[{request_id}] Error processing prop {prop.get('id', 'unknown')}: {e}")
                    validation_issues += 1
                    continue
            
            # Add sport and league fields to each prop (required by Pydantic model)
            for prop in validated_props:
                if 'sport' not in prop or not prop['sport']:
                    prop['sport'] = 'NBA' if 'basketball' in sport_key else \
                                   'NFL' if 'football' in sport_key else \
                                   'NHL' if 'hockey' in sport_key else \
                                   'MLB' if 'baseball' in sport_key else \
                                   'Soccer' if 'soccer' in sport_key else 'Unknown'
                if 'league' not in prop or not prop['league']:
                    prop['league'] = sport_key.split('_')[-1].upper() if '_' in sport_key else sport_key.upper()
            
            logger.info(f"[{request_id}] Successfully validated {len(validated_props)}/{len(props)} props (issues: {validation_issues})")
            return validated_props
            
        # If no props from ESPN, return empty list
        logger.info(f"[{request_id}] No props found, returning empty list")
        return []
        
    except HTTPException:
        raise
    except asyncio.TimeoutError:
        logger.error(f"[{request_id}] Timeout getting player props for {sport_key}/{event_id}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request timed out while fetching player props"
        )
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error getting player props: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get player props: {str(e)}"
        )

@router.get("/anytime-goal-scorers/{sport_key}/{event_id}")
async def get_anytime_goal_scorers(
    sport_key: str,
    event_id: str,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get top 2 likely scorers from each team for Anytime Goal unlock"""
    request_id = f"anytime_goal_{sport_key}_{event_id}_{datetime.utcnow().timestamp()}"
    logger.info(f"[{request_id}] Getting anytime goal scorers for {sport_key}/{event_id} - User: {current_user_id}")
    
    try:
        # Get user's tier first
        try:
            result = await db.execute(select(User).where(User.id == current_user_id))
            user = result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[{request_id}] Database error fetching user: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
        
        normalized_tier = 'starter'
        if user:
            normalized_tier = (user.subscription_tier or 'starter').lower().strip()
            logger.info(f"[{request_id}] User tier: {normalized_tier}")
        
        # Check tier features - anytime goal data requires at least basic tier
        if normalized_tier == 'starter':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anytime Goal data available to Basic tier and above"
            )
        
        # Get sport league for context
        league = 'NHL' if 'hockey' in sport_key else \
                 'NBA' if 'basketball' in sport_key else \
                 'NFL' if 'football' in sport_key else \
                 'MLB' if 'baseball' in sport_key else \
                 'Soccer' if 'soccer' in sport_key else 'Unknown'
        
        logger.info(f"[{request_id}] Fetching anytime goal scorers for {league}")
        try:
            scorers = await get_espn_service().get_anytime_goal_scorers(sport_key, event_id, league)
            logger.info(f"[{request_id}] Successfully fetched anytime goal scorers")
            return scorers
        except asyncio.TimeoutError:
            logger.error(f"[{request_id}] Timeout fetching anytime goal scorers")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Request timed out while fetching anytime goal data"
            )
        except Exception as e:
            logger.error(f"[{request_id}] Error fetching anytime goal scorers: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch anytime goal data: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get anytime goal scorers"
        )

@router.get("/game/{sport_key}/{event_id}/full")
async def get_game_full_props(
    sport_key: str,
    event_id: str,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get unified player props for frontend integration (all sports).
    Returns organized props by type: goals, assists, anytime_goal, team_props, etc.
    Enriches props with is_locked status and user's daily picks info.
    """
    request_id = f"full_props_{sport_key}_{event_id}_{datetime.utcnow().timestamp()}"
    logger.info(f"[{request_id}] Getting full props for {sport_key}/{event_id} - User: {current_user_id}")
    
    try:
        # Get user tier and daily picks info for tier gating
        try:
            result = await db.execute(select(User).where(User.id == current_user_id))
            user = result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[{request_id}] Database error fetching user: {e}")
            user = None
        
        normalized_tier = 'starter'
        if user:
            normalized_tier = str(user.subscription_tier or 'starter').lower().strip().replace('\\\\', '').replace('\"', '')
        
        try:
            tier_config = TierFeatures.get_tier_config(normalized_tier)
            daily_limit = tier_config.get('predictions_per_day') or 999999
            daily_picks_used = await get_prediction_service().get_daily_picks_count(db, current_user_id)
        except Exception as e:
            logger.error(f"[{request_id}] Error getting daily picks count: {e}")
            daily_limit = 1
            daily_picks_used = 0
        
        # Get tier features
        tier_features = get_tier_features(normalized_tier)
        
        # Support all sports - endpoint works with any sport_key and filters props dynamically
        logger.info(f"[{request_id}] Processing props for sport: {sport_key}")
        
        # Fetch all props for this game with increased timeout
        # Soccer needs longer timeout due to complex API calls
        is_soccer = 'soccer' in sport_key.lower()
        fetch_timeout = 180.0 if is_soccer else 120.0
        
        try:
            all_props = await asyncio.wait_for(
                get_espn_service().get_player_props(sport_key, event_id),
                timeout=fetch_timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"[{request_id}] Props fetch timed out after {fetch_timeout}s for {sport_key}, using empty list")
            all_props = []
        except Exception as e:
            logger.warning(f"[{request_id}] Error fetching props for {sport_key}: {e}")
            all_props = []
        
        logger.info(f"[{request_id}] Received {len(all_props)} props from get_player_props")
        
        # CRITICAL DEBUG: Check if props are empty and why
        if not all_props:
            logger.error(f"[{request_id}] ❌ CRITICAL: all_props is EMPTY for {sport_key}/{event_id}! This should never happen - FIFA should have props!")
            logger.error(f"[{request_id}] Check backend logs for errors in _get_player_props_internal")
        else:
            logger.info(f"[{request_id}] ✅ Got {len(all_props)} props")
            logger.info(f"[{request_id}] Props sample: First prop market_key={all_props[0].get('market_key', 'NO_KEY')}, player={all_props[0].get('player', 'NO_PLAYER')}")
            logger.info(f"[{request_id}] Market keys in all_props: {set(p.get('market_key', 'NO_KEY') for p in all_props)}")
        
        # Enrich all props with user's follow status and daily picks info
        for prop in all_props:
            try:
                # Add daily picks info
                prop['daily_picks_used'] = daily_picks_used
                prop['daily_picks_limit'] = daily_limit
                
                # Check if user is already following this prediction
                prop_id = prop.get('id', '')
                if prop_id:
                    try:
                        is_following = await get_prediction_service().is_following_prediction(db, current_user_id, prop_id)
                        prop['is_locked'] = not is_following
                        logger.info(f"[{request_id}] Checked follow status - Prop: {prop_id}, User: {current_user_id}, is_following={is_following}, is_locked={prop['is_locked']}")
                        if is_following:
                            logger.info(f"[{request_id}] ✅ Prop {prop_id} IS UNLOCKED for user {current_user_id}")
                        else:
                            logger.info(f"[{request_id}] 🔒 Prop {prop_id} IS LOCKED for user {current_user_id}")
                    except Exception as e:
                        logger.error(f"[{request_id}] Error checking follow status for {prop_id}: {e}", exc_info=True)
                        prop['is_locked'] = True
                else:
                    logger.warning(f"[{request_id}] Prop has no ID: {prop}")
                    prop['is_locked'] = True
                
                # For Pro/Pro Plus/Elite users, always show models
                # For lower tiers, only show models if already following (unlocked)
                show_all = normalized_tier in ['pro', 'pro_plus', 'elite'] or not prop.get('is_locked', True)
                
                if not show_all:
                    if not tier_features['show_odds']:
                        prop['odds'] = None
                    if not tier_features['show_reasoning']:
                        prop['reasoning'] = None
                    if not tier_features['show_models']:
                        prop['models'] = None
            except Exception as e:
                logger.warning(f"[{request_id}] Error enriching prop {prop.get('id', 'unknown')}: {e}")
                # Don't skip the prop, just log the error
                prop['is_locked'] = True
        
        # Organize by type - NHL/Soccer have goals/assists, other sports may have different types
        goals_props = [p for p in all_props if p.get("market_key") == "goals"]
        assists_props = [p for p in all_props if p.get("market_key") == "assists"]
        
        # Player-level anytime goal props (if any exist, for backward compatibility)
        anytime_goal_props = [p for p in all_props if p.get("market_key") == "anytime_goal"]
        
        # Team-level props (game totals + team anytime goal)
        team_props = [p for p in all_props if p.get("market_key") in ["game_total", "anytime_goal_team"]]
        
        # For other sports (NBA/MLB), collect other market types
        other_props = [p for p in all_props if p.get("market_key") not in ["goals", "assists", "anytime_goal", "game_total", "anytime_goal_team"]]
        
        logger.info(f"[{request_id}] ✅ SOCCER PROPS BREAKDOWN - Sport: {sport_key}")
        logger.info(f"[{request_id}]   Goals Props: {len(goals_props)}")
        if goals_props:
            logger.info(f"[{request_id}]     Sample: {goals_props[0].get('player', 'UNKNOWN')} - {goals_props[0].get('market_name', 'N/A')}")
        logger.info(f"[{request_id}]   Assists Props: {len(assists_props)}")
        if assists_props:
            logger.info(f"[{request_id}]     Sample: {assists_props[0].get('player', 'UNKNOWN')} - {assists_props[0].get('market_name', 'N/A')}")
        logger.info(f"[{request_id}]   Anytime Goal Props: {len(anytime_goal_props)}")
        logger.info(f"[{request_id}]   Team Props: {len(team_props)}")
        logger.info(f"[{request_id}]   Other Props: {len(other_props)}")
        
        # Determine sport name based on sport_key
        sport_name = "Unknown"
        if "hockey" in sport_key:
            sport_name = "NHL"
        elif "soccer" in sport_key:
            sport_name = "Soccer"
        elif "basketball_nba" in sport_key:
            sport_name = "NBA"
        elif "basketball_ncaa" in sport_key:
            sport_name = "NCAAB"
        elif "baseball_mlb" in sport_key:
            sport_name = "MLB"
        elif "football_nfl" in sport_key:
            sport_name = "NFL"
        
        # For Soccer (and NHL), fetch anytime goal scorers for the unlock feature
        anytime_goal_scorers = None
        if "soccer" in sport_key or "hockey" in sport_key:
            try:
                scorer_data = await get_espn_service().get_anytime_goal_scorers(sport_key, event_id, sport_name)
                if scorer_data and scorer_data.get("home_team"):
                    anytime_goal_scorers = {
                        "home_team": scorer_data.get("home_team", {}),
                        "away_team": scorer_data.get("away_team", {}),
                        "source": scorer_data.get("data_source", "Props Extraction")
                    }
                    logger.info(f"[{request_id}] Got anytime goal scorers for {sport_key}")
            except Exception as e:
                logger.debug(f"[{request_id}] Could not fetch anytime goal scorers: {e}")
        
        return {
            "event_id": event_id,
            "sport_key": sport_key,
            "sport": sport_name,
            "props_summary": {
                "total_goals": len(goals_props),
                "total_assists": len(assists_props),
                "total_anytime_goals": len(anytime_goal_props),
                "total_team_props": len(team_props),
                "total_other_props": len(other_props),
                "total_all_props": len(all_props),
                "total_players": len(set(p.get("player") for p in all_props if p.get("player")))
            },
            "goals": goals_props,
            "assists": assists_props,
            "anytime_goal": anytime_goal_props,  # Backward compatibility (NHL/Soccer)
            "anytime_goal_scorers": anytime_goal_scorers,  # 2 scorers from each team with reasoning
            "team_props": team_props,  # Game totals + anytime goal team (NHL/Soccer)
            "other_props": other_props,  # Other market types (NBA/MLB)
            "all_props": all_props,  # All props (fallback for UI)
            "updated_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error getting full props: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get game props: {str(e)}"
        )

@router.get("/player-props", response_model=List[PredictionResponse])
async def get_player_props_query(
    sport_key: str = Query(..., description="Sport key (e.g., basketball_nba)"),
    event_id: str = Query(..., description="Event ID"),
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get player props via query parameters (for Dashboard)"""
    request_id = f"query_{sport_key}_{event_id}_{datetime.utcnow().timestamp()}"
    logger.info(f"[{request_id}] Getting player props (query) for {sport_key}/{event_id} - User: {current_user_id}")
    
    try:
        # Get user's tier and daily picks info
        try:
            result = await db.execute(select(User).where(User.id == current_user_id))
            user = result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[{request_id}] Database error fetching user: {e}")
            user = None
        
        normalized_tier = 'starter'
        if user:
            normalized_tier = str(user.subscription_tier or 'starter').lower().strip().replace('\\\\', '').replace('\"', '')
        
        try:
            tier_config = TierFeatures.get_tier_config(normalized_tier)
            daily_limit = tier_config.get('predictions_per_day') or 999999
            daily_picks_used = await get_prediction_service().get_daily_picks_count(db, current_user_id)
        except Exception as e:
            logger.error(f"[{request_id}] Error getting daily picks count: {e}")
            daily_limit = 1
            daily_picks_used = 0
        
        # Get tier features
        tier_features = get_tier_features(normalized_tier)
        
        # Fetch game data to get matchup info
        game_data = None
        try:
            games = await get_espn_service().get_upcoming_games(sport_key)
            for game in games:
                if game.get("id") == event_id:
                    game_data = game
                    break
            if game_data:
                logger.info(f"[{request_id}] Found game data for matchup")
            else:
                logger.warning(f"[{request_id}] Game {event_id} not found in upcoming games")
        except Exception as e:
            logger.warning(f"[{request_id}] Could not fetch game data: {e}")
        
        # Try ESPN service first
        logger.info(f"[{request_id}] Calling ESPN service for player props")
        props = None
        espn_error = None
        
        try:
            props = await get_espn_service().get_player_props(sport_key, event_id)
            logger.info(f"[{request_id}] ESPN service returned {len(props)} props")
        except asyncio.TimeoutError as e:
            logger.warning(f"[{request_id}] Timeout calling ESPN service: {e}")
            espn_error = "timeout"
        except Exception as e:
            logger.warning(f"[{request_id}] Error calling ESPN service: {e}", exc_info=True)
            espn_error = str(e)
        
        # If ESPN service failed or returned no props, generate fallback props
        if not props:
            logger.warning(f"[{request_id}] ESPN service unavailable or no props returned - returning empty list (NO MOCK DATA)")
            props = []
        
        if props:
            # Get matchup from game data
            matchup = "Unknown Matchup"
            if game_data:
                home_team = game_data.get('home_team', {}).get('name', 'Home')
                away_team = game_data.get('away_team', {}).get('name', 'Away')
                matchup = f"{away_team} @ {home_team}"
            
            # Add sport and league fields to each prop (required by Pydantic model)
            for prop in props:
                if 'sport' not in prop or not prop['sport']:
                    prop['sport'] = 'NBA' if 'basketball' in sport_key else \
                                   'NFL' if 'football' in sport_key else \
                                   'NHL' if 'hockey' in sport_key else \
                                   'MLB' if 'baseball' in sport_key else \
                                   'Soccer' if 'soccer' in sport_key else 'Unknown'
                if 'league' not in prop or not prop['league']:
                    prop['league'] = sport_key.split('_')[-1].upper() if '_' in sport_key else sport_key.upper()
                # Add missing required fields
                if 'matchup' not in prop:
                    prop['matchup'] = matchup
                if 'prediction_type' not in prop:
                    prop['prediction_type'] = 'player_prop'
                if 'created_at' not in prop:
                    prop['created_at'] = datetime.utcnow().isoformat()
                # Convert odds to string if it's an int
                if 'odds' in prop and isinstance(prop['odds'], int):
                    prop['odds'] = str(prop['odds'])
                # Convert odds to string if it's an int
                if 'odds' in prop and isinstance(prop['odds'], int):
                    prop['odds'] = str(prop['odds'])
            
            # Add daily picks info and check following status for each prop
            for prop in props:
                try:
                    prop['daily_picks_used'] = daily_picks_used
                    prop['daily_picks_limit'] = daily_limit
                    
                    # Check if user is already following this prediction
                    prop_id = prop.get('id', '')
                    if prop_id:
                        try:
                            is_following = await get_prediction_service().is_following_prediction(db, current_user_id, prop_id)
                            prop['is_locked'] = not is_following
                        except Exception as e:
                            logger.warning(f"[{request_id}] Error checking follow status for {prop_id}: {e}")
                            prop['is_locked'] = True
                    
                    # For Pro/Pro Plus/Elite users, always show models
                    # For lower tiers, only show models if already following (unlocked)
                    show_all = normalized_tier in ['pro', 'pro_plus', 'elite'] or not prop.get('is_locked', True)
                    
                    if not show_all:
                        if not tier_features['show_odds']:
                            prop['odds'] = None
                        if not tier_features['show_reasoning']:
                            prop['reasoning'] = None
                        if not tier_features['show_models']:
                            prop['models'] = None
                except Exception as e:
                    logger.warning(f"[{request_id}] Error processing prop {prop.get('id', 'unknown')}: {e}")
                    continue
            
            return props
            
        # If no props from ESPN, return empty list
        logger.info(f"[{request_id}] No props found, returning empty list")
        return []
        
    except HTTPException:
        raise
    except asyncio.TimeoutError:
        logger.error(f"[{request_id}] Timeout getting player props for {sport_key}/{event_id}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request timed out while fetching player props"
        )
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error getting player props: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get player props: {str(e)}"
        )

@router.get("/", response_model=PredictionsListResponse)
async def get_predictions(
    sport: Optional[str] = None,
    league: Optional[str] = None,
    min_confidence: float = 0.0,
    limit: int = 10,
    offset: int = 0,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get predictions with tier-based feature gating"""
    try:
        logger.info(f"[GET_PREDICTIONS] Starting request for user {current_user_id}, sport={sport}, limit={limit}")
        
        # Get user
        result = await db.execute(select(User).where(User.id == current_user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"[GET_PREDICTIONS] Got user {user.id}, tier {user.subscription_tier}")
        
        # Get predictions from service
        logger.info(f"[GET_PREDICTIONS] Calling prediction service...")
        
        predictions = await get_prediction_service().get_predictions(
            db=db,
            user=user,
            sport=sport,
            league=league,
            min_confidence=min_confidence,
            limit=limit,
            offset=offset
        )
        
        logger.info(f"[GET_PREDICTIONS] Service returned {len(predictions)} predictions")
        
        # Get user's tier and daily picks info
        normalized_tier = (user.subscription_tier or 'starter').lower().strip()
        
        # Use TIER_LIMITS from prediction_service
        daily_limit = get_prediction_service().TIER_LIMITS.get(normalized_tier, 1)
        daily_picks_used = await get_prediction_service().get_daily_picks_count(db, current_user_id)
        
        logger.info(f"[GET_PREDICTIONS] Tier: {normalized_tier}, daily used: {daily_picks_used}/{daily_limit}")
        
        # Get tier features
        tier_features = get_tier_features(normalized_tier)
        
        # Apply feature gating to each prediction
        gated_predictions = []
        for pred in predictions:
            # ===== CLUB 100 ACCESS CHECK =====
            is_club_100_pick = pred.get('is_club_100_pick', False)
            if is_club_100_pick and not user.club_100_unlocked:
                # User doesn't have Club 100 access - filter out this prediction
                logger.info(f"[GET_PREDICTIONS] Filtering Club 100 prediction {pred['id']} - user not unlocked")
                continue
            
            # Check if user is already following this prediction
            is_following = await get_prediction_service().is_following_prediction(db, current_user_id, pred['id'])
            
            gated_pred = pred.copy()
            gated_pred['is_locked'] = not is_following
            gated_pred['daily_picks_used'] = daily_picks_used
            gated_pred['daily_picks_limit'] = daily_limit
            gated_pred['club_100_unlocked'] = user.club_100_unlocked  # For frontend reference
            
            # For Pro/Pro Plus/Elite users, always show all features
            # For lower tiers, apply gating
            show_all = normalized_tier in ['pro', 'pro_plus', 'elite'] or is_following
            
            if not show_all:
                if not tier_features['show_odds']:
                    gated_pred['odds'] = None
                if not tier_features['show_reasoning']:
                    gated_pred['reasoning'] = None
                if not tier_features['show_models']:
                    gated_pred['models'] = None
            
            gated_predictions.append(gated_pred)
        
        logger.info(f"[GET_PREDICTIONS] Returning {len(gated_predictions)} gated predictions")
        return {"predictions": gated_predictions}

    except asyncio.TimeoutError:
        logger.error(f"Timeout fetching predictions for {sport}/{league}", exc_info=True)
        raise HTTPException(
            status_code=504,
            detail="Prediction service timed out. Please try again."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get predictions"
        )

# Additional route to support no trailing slash (for clients that drop slash)
@router.get("", response_model=PredictionsListResponse, include_in_schema=False)
async def get_predictions_no_slash(
    sport: Optional[str] = None,
    league: Optional[str] = None,
    min_confidence: float = 0.0,
    limit: int = 10,
    offset: int = 0,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await get_predictions(sport=sport, league=league, min_confidence=min_confidence, limit=limit, offset=offset, current_user_id=current_user_id, db=db)

@router.post("/{prediction_id}/follow")
async def follow_prediction(
    prediction_id: str,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    sport_key: Optional[str] = Query(None, description="Sport key for the prediction"),
    prediction_data: Dict[str, Any] = Body({}, description="Prediction data for player props"),
    is_club_100_pick: Optional[bool] = Query(False, description="Whether this is a Club 100 pick (costs 5 picks instead of 1)")
):
    """Follow/unlock a prediction (game pick or player prop). Club 100 picks cost 5 daily picks instead of 1."""
    request_id = f"{prediction_id}_{datetime.utcnow().timestamp()}"
    logger.info(f"[FOLLOW_DEBUG][{request_id}] ✅ FOLLOW REQUEST RECEIVED")
    logger.info(f"[FOLLOW_DEBUG][{request_id}]   prediction_id: {prediction_id} (type: {type(prediction_id).__name__})")
    logger.info(f"[FOLLOW_DEBUG][{request_id}]   current_user_id: {current_user_id}")
    logger.info(f"[FOLLOW_DEBUG][{request_id}]   is_club_100_pick: {is_club_100_pick}")
    logger.info(f"[FOLLOW_DEBUG][{request_id}]   sport_key (query param): {sport_key}")
    logger.info(f"[FOLLOW_DEBUG][{request_id}]   prediction_data type: {type(prediction_data).__name__}")
    logger.info(f"[FOLLOW_DEBUG][{request_id}]   prediction_data keys: {list(prediction_data.keys()) if isinstance(prediction_data, dict) else 'N/A'}")
    logger.info(f"[FOLLOW_DEBUG][{request_id}]   prediction_data full content: {prediction_data}")
    
    # Validate prediction_data structure
    if isinstance(prediction_data, dict) and not prediction_data.get('id'):
        logger.warning(f"[FOLLOW_DEBUG][{request_id}] ⚠️ WARNING: prediction_data does not have 'id' field")
        logger.warning(f"[FOLLOW_DEBUG][{request_id}]   prediction_id parameter will be used instead")
    
    try:
        # Check if this is a player prop using improved detection
        is_player_prop = is_player_prop_id(prediction_id)
        logger.info(f"[FOLLOW_DEBUG][{request_id}] Is player prop: {is_player_prop}")
        
        # Get user's tier and daily picks info
        try:
            result = await db.execute(select(User).where(User.id == current_user_id))
            user = result.scalar_one_or_none()
            normalized_tier = str(user.subscription_tier or 'starter').lower().strip().replace('\\\\', '').replace('\"', '') if user else 'starter'
            daily_picks_used = await get_prediction_service().get_daily_picks_count(db, current_user_id)
            tier_config = TierFeatures.get_tier_config(normalized_tier)
            
            # CRITICAL: Check for None tier_config before calling .get()
            if not tier_config:
                logger.warning(f"[FOLLOW_DEBUG][{request_id}] ⚠️ tier_config is None for tier '{normalized_tier}'! Using default limit of 1.")
                daily_limit = 1
            else:
                daily_limit = tier_config.get('predictions_per_day')
                if daily_limit is None:
                    logger.warning(f"[FOLLOW_DEBUG][{request_id}] ⚠️ predictions_per_day is None in tier_config! Using default limit of 1.")
                    daily_limit = 1
            
            logger.info(f"[FOLLOW_DEBUG][{request_id}] User tier: {normalized_tier}, picks used today: {daily_picks_used}, daily limit: {daily_limit}, picks after this: {daily_picks_used + 1}")
        except Exception as e:
            logger.error(f"[FOLLOW_DEBUG][{request_id}] Error getting user tier: {e}", exc_info=True)
            normalized_tier = 'starter'
            daily_picks_used = 0
            daily_limit = 1
        
        # Determine pick cost: 5 for Club 100, 1 for regular picks
        pick_cost = 5 if is_club_100_pick else 1
        logger.info(f"[FOLLOW_DEBUG][{request_id}] Pick cost: {pick_cost} (is_club_100_pick={is_club_100_pick})")
        
        # For player props - use provided prediction_data or extract from prediction_id
        if is_player_prop:
            logger.info(f"[FOLLOW_DEBUG][{request_id}] Processing player prop")
            
            # If no prediction_data or missing player field, try to extract from prediction_id
            if not prediction_data or not prediction_data.get('player'):
                logger.info(f"[FOLLOW_DEBUG][{request_id}] No prediction_data provided, extracting from prediction_id")
                
                parsed = parse_player_prop_id(prediction_id)
                if not parsed:
                    logger.error(f"[FOLLOW_DEBUG][{request_id}] Could not parse player prop ID: {prediction_id}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid player prop ID format"
                    )
                
                # Build minimal prediction_data from parsed info
                prediction = {
                    'id': prediction_id,
                    'event_id': parsed.get('event_id'),
                    'market_key': parsed.get('market_key'),
                    'player': parsed.get('player_name'),
                    'prediction': f"{parsed.get('player_name')} - {parsed.get('market_key').replace('_', ' ').title()}",
                    'sport_key': sport_key,  # Include sport_key if provided
                }
                logger.info(f"[FOLLOW_DEBUG][{request_id}] Built prediction from ID: player={parsed.get('player_name')}, market={parsed.get('market_key')}")
            else:
                # Use provided prediction_data
                prediction = prediction_data
                prediction['id'] = prediction_id
        else:
            # For regular predictions - fetch from ESPN or use provided data
            logger.info(f"[FOLLOW_DEBUG][{request_id}] Processing regular prediction")
            
            if prediction_data and prediction_data.get('id'):
                # Use provided prediction data
                logger.info(f"[FOLLOW_DEBUG][{request_id}] Using provided prediction_data")
                prediction = prediction_data
                prediction['id'] = prediction_id
            elif sport_key:
                try:
                    logger.info(f"[FOLLOW_DEBUG][{request_id}] Fetching from ESPN service with sport_key={sport_key}")
                    prediction = await get_espn_service().get_prediction_by_id(prediction_id, sport_key)
                    if not prediction:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Prediction {prediction_id} not found"
                        )
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"[FOLLOW_DEBUG][{request_id}] Error fetching from ESPN: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Error fetching prediction: {str(e)}"
                    )
            else:
                logger.error(f"[FOLLOW_DEBUG][{request_id}] Missing both prediction_data and sport_key for regular prediction")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either prediction_data or sport_key required"
                )
        
        # Check if user already following
        try:
            already_following = await get_prediction_service().is_following_prediction(
                db=db,
                user_id=current_user_id,
                prediction_id=prediction_id
            )
            logger.info(f"[FOLLOW_DEBUG][{request_id}] Already following: {already_following}")
        except Exception as e:
            logger.error(f"[FOLLOW_DEBUG][{request_id}] Error checking is_following: {e}")
            already_following = False
        
        if already_following:
            logger.info(f"[FOLLOW_DEBUG][{request_id}] Already following - returning existing data")
            prediction['is_locked'] = False
            return prediction
        
        # Check if user has enough daily picks for this pick
        # Allow unlimited picks for pro_plus and elite tiers
        picks_after_follow = daily_picks_used + pick_cost
        if normalized_tier not in ['elite', 'pro_plus'] and picks_after_follow > daily_limit:
            logger.warning(f"[FOLLOW_DEBUG][{request_id}] Not enough picks. Used: {daily_picks_used}, Need: {pick_cost}, Limit: {daily_limit}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough daily picks. You have {daily_limit - daily_picks_used} picks left, but need {pick_cost}. Upgrade your plan for more picks!"
            )
        
        
        # Follow the prediction
        try:
            logger.info(f"[FOLLOW_DEBUG][{request_id}] Calling follow_prediction service with is_club_100_pick={is_club_100_pick}")
            result = await get_prediction_service().follow_prediction(
                db=db,
                user_id=current_user_id,
                prediction_data=prediction,
                is_club_100_pick=is_club_100_pick
            )
            logger.info(f"[FOLLOW_DEBUG][{request_id}] follow_prediction returned: {result}")
            
            # After recording the follow, verify it was saved
            try:
                verify_following = await get_prediction_service().is_following_prediction(db, current_user_id, prediction_id)
                logger.info(f"[FOLLOW_DEBUG][{request_id}] ✅ VERIFICATION: is_following_prediction returned {verify_following} for {prediction_id}")
            except Exception as verify_err:
                logger.error(f"[FOLLOW_DEBUG][{request_id}] ❌ VERIFICATION FAILED: {verify_err}")
        except ValueError as e:
            logger.error(f"[FOLLOW_DEBUG][{request_id}] ❌ ValueError in follow_prediction: {str(e)}", exc_info=True)
            error_detail = str(e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not follow prediction: {error_detail}"
            )
        except Exception as e:
            logger.error(f"[FOLLOW_DEBUG][{request_id}] ❌ Unexpected error in follow_prediction: {type(e).__name__}: {str(e)}", exc_info=True)
            error_detail = f"{type(e).__name__}: {str(e)}"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not follow prediction: {error_detail}"
            )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not follow prediction"
            )
        
        # Return the unlocked prediction data
        prediction['is_locked'] = False
        prediction['daily_picks_used'] = daily_picks_used + pick_cost
        prediction['daily_picks_limit'] = daily_limit
        prediction['is_club_100_pick'] = is_club_100_pick
        prediction['pick_cost'] = pick_cost
        
        # For anytime goal props, fetch and include the player scorers
        if is_player_prop and prediction_data and prediction_data.get('market_key') == 'anytime_goal':
            logger.info(f"[FOLLOW_DEBUG][{request_id}] 🎯 ANYTIME GOAL UNLOCK DETECTED")
            logger.info(f"[FOLLOW_DEBUG][{request_id}]   is_player_prop={is_player_prop}, has prediction_data={prediction_data is not None}")
            logger.info(f"[FOLLOW_DEBUG][{request_id}]   market_key={prediction_data.get('market_key')}")
            logger.info(f"[FOLLOW_DEBUG][{request_id}]   sport_key={sport_key}, event_id={prediction_data.get('event_id')}")
            
            try:
                # Get the league from prediction data or sport_key
                league = 'NHL' if 'hockey' in sport_key else \
                         'NBA' if 'basketball' in sport_key else \
                         'NFL' if 'football' in sport_key else \
                         'MLB' if 'baseball' in sport_key else \
                         'Soccer' if 'soccer' in sport_key else 'Unknown'
                
                logger.info(f"[FOLLOW_DEBUG][{request_id}]   league={league}")
                logger.info(f"[FOLLOW_DEBUG][{request_id}] Calling get_espn_service().get_anytime_goal_scorers({sport_key}, {prediction_data.get('event_id')}, {league})")
                
                scorers_data = await get_espn_service().get_anytime_goal_scorers(sport_key, prediction_data.get('event_id'), league)
                
                logger.info(f"[FOLLOW_DEBUG][{request_id}] Scorers data returned: {scorers_data is not None}")
                logger.info(f"[FOLLOW_DEBUG][{request_id}] Scorers data type: {type(scorers_data)}")
                if scorers_data:
                    logger.info(f"[FOLLOW_DEBUG][{request_id}] Scorers data keys: {list(scorers_data.keys())}")
                    logger.info(f"[FOLLOW_DEBUG][{request_id}] Full scorers data: {scorers_data}")
                
                # Add scorers to the prediction response
                if scorers_data:
                    prediction['anytime_goal_scorers'] = scorers_data
                    
                    # Build a display string showing all 4 scorers
                    home_scorers = scorers_data.get('home_team', {}).get('top_scorers', [])
                    away_scorers = scorers_data.get('away_team', {}).get('top_scorers', [])
                    
                    logger.info(f"[FOLLOW_DEBUG][{request_id}] Home scorers: {len(home_scorers)}, Away scorers: {len(away_scorers)}")
                    
                    scorer_names = []
                    for scorer in home_scorers[:2]:
                        name = scorer.get('player', 'Unknown')
                        scorer_names.append(name)
                        logger.info(f"[FOLLOW_DEBUG][{request_id}]   Added home scorer: {name}")
                    for scorer in away_scorers[:2]:
                        name = scorer.get('player', 'Unknown')
                        scorer_names.append(name)
                        logger.info(f"[FOLLOW_DEBUG][{request_id}]   Added away scorer: {name}")
                    
                    prediction['anytime_goal_names'] = scorer_names
                    prediction['prediction'] = f"Likely Scorers: {', '.join(scorer_names)}"
                    logger.info(f"[FOLLOW_DEBUG][{request_id}] ✅ ANYTIME GOAL SCORERS ADDED: {scorer_names}")
                else:
                    logger.warning(f"[FOLLOW_DEBUG][{request_id}] ❌ Scorers data is empty/None")
            except Exception as e:
                logger.error(f"[FOLLOW_DEBUG][{request_id}] ❌ Could not fetch anytime goal scorers: {e}", exc_info=True)
                # Don't fail the whole unlock, just skip adding scorers
                pass
        else:
            if not is_player_prop:
                logger.debug(f"[FOLLOW_DEBUG][{request_id}] Not a player prop (is_player_prop={is_player_prop})")
            elif not prediction_data:
                logger.debug(f"[FOLLOW_DEBUG][{request_id}] No prediction_data provided")
            elif prediction_data.get('market_key') != 'anytime_goal':
                logger.debug(f"[FOLLOW_DEBUG][{request_id}] Not anytime_goal market (market_key={prediction_data.get('market_key')})")
        
        # Apply tier-based filtering for NEW unlocks
        if normalized_tier not in ['pro', 'pro_plus', 'elite']:
            tier_features = get_tier_features(normalized_tier)
            if not tier_features['show_odds']:
                prediction.pop('odds', None)
            if not tier_features['show_reasoning']:
                prediction.pop('reasoning', None)
            if not tier_features['show_models']:
                prediction.pop('models', None)
        
        logger.info(f"[FOLLOW_DEBUG][{request_id}] Successfully unlocked prediction")
        return prediction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FOLLOW_DEBUG][{request_id}] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{prediction_id}/unfollow")
async def unfollow_prediction(
    prediction_id: str,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Unfollow a prediction"""
    result = await get_prediction_service().unfollow_prediction(
        db=db,
        user_id=current_user_id,
        prediction_id=prediction_id
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not unfollow prediction"
        )
    return {"success": True, "message": "Prediction unfollowed"}


# ====== CLUB 100 ENDPOINTS ======
@router.get("/club-100/status")
async def get_club_100_status(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Club 100 unlock status for current user"""
    try:
        from app.services.club_100_service import Club100Service
        service = Club100Service()
        status_info = await service.check_user_club_100_status(db, current_user_id)
        return status_info
    except Exception as e:
        logger.error(f"Error checking Club 100 status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check Club 100 status"
        )


@router.get("/club-100/can-unlock")
async def can_unlock_club_100(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if user can unlock Club 100 (has enough picks available)"""
    try:
        logger.info(f"[Club100] Checking unlock eligibility for user: {current_user_id}")
        
        # Get user
        result = await db.execute(select(User).where(User.id == current_user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Get tier config
        normalized_tier = (user.subscription_tier or 'starter').lower().strip()
        tier_config = TierFeatures.get_tier_config(normalized_tier)
        
        if not tier_config:
            tier_config = TierFeatures.get_tier_config('starter')
        
        daily_limit = tier_config.get('predictions_per_day', 1) if tier_config else 1
        
        # Count daily picks used (excluding prior Club 100 access picks)
        from app.models.db_models import user_predictions, Prediction
        from datetime import timezone
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        daily_picks_stmt = select(func.count()).select_from(user_predictions).join(
            Prediction, user_predictions.c.prediction_id == Prediction.id
        ).where(
            and_(
                user_predictions.c.user_id == current_user_id,
                Prediction.created_at >= today_start,
                Prediction.sport != 'club_100_access'
            )
        )
        
        daily_picks_result = await db.execute(daily_picks_stmt)
        daily_picks_used = daily_picks_result.scalar() or 0
        
        CLUB_100_ACCESS_COST = 5
        picks_available = daily_limit - daily_picks_used
        can_unlock = picks_available >= CLUB_100_ACCESS_COST or normalized_tier in ['pro_plus', 'elite']
        
        return {
            "can_unlock": can_unlock,
            "unlocked": user.club_100_unlocked or False,
            "daily_picks_used": daily_picks_used,
            "daily_picks_available": picks_available,
            "daily_picks_limit": daily_limit,
            "access_cost": CLUB_100_ACCESS_COST,
            "tier": {
                "name": tier_config.get('name', 'Unknown'),
                "description": tier_config.get('description', ''),
                "has_unlimited_picks": normalized_tier in ['pro_plus', 'elite']
            },
            "reason": "User has enough picks" if can_unlock else f"Need {CLUB_100_ACCESS_COST} picks, but only have {picks_available} available"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking Club 100 unlock eligibility: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check Club 100 eligibility: {str(e)}"
        )


@router.post("/club-100/unlock")
async def unlock_club_100(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check Club 100 access eligibility - requires 5 available daily picks, no unlock needed"""
    try:
        logger.info(f"[Club100] Status check for user: {current_user_id}")
        
        # Get user
        result = await db.execute(select(User).where(User.id == current_user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Get tier config
        normalized_tier = (user.subscription_tier or 'starter').lower().strip()
        tier_config = TierFeatures.get_tier_config(normalized_tier)
        if not tier_config:
            tier_config = TierFeatures.get_tier_config('starter')
        
        daily_limit = tier_config.get('predictions_per_day', 1) if tier_config else 1
        logger.info(f"[Club100] Tier: {normalized_tier}, daily limit: {daily_limit}")
        
        # Check if unlimited tier (PRO_PLUS, ELITE)
        if normalized_tier in ['pro_plus', 'elite']:
            return {
                "eligible": True,
                "message": f"✅ Your {tier_config.get('name', 'Elite')} tier has unlimited picks!",
                "picks_available": 9999,
                "picks_needed": 5,
                "tier": normalized_tier
            }
        
        # Count daily picks used TODAY - EXCLUDE Club 100 access picks
        from app.models.db_models import user_predictions, Prediction
        from datetime import timezone
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        daily_picks_stmt = select(func.count()).select_from(user_predictions).join(
            Prediction, user_predictions.c.prediction_id == Prediction.id
        ).where(
            and_(
                user_predictions.c.user_id == current_user_id,
                Prediction.created_at >= today_start,
                Prediction.sport != 'club_100_access'
            )
        )
        
        daily_picks_result = await db.execute(daily_picks_stmt)
        daily_picks_used = daily_picks_result.scalar() or 0
        picks_available = daily_limit - daily_picks_used
        
        logger.info(f"[Club100] User {current_user_id}: used {daily_picks_used}, available {picks_available}")
        
        CLUB_100_COST = 5
        eligible = picks_available >= CLUB_100_COST
        
        if eligible:
            return {
                "eligible": True,
                "message": f"✅ You have {picks_available} picks available! Club 100 access is ready.",
                "picks_available": picks_available,
                "picks_needed": CLUB_100_COST,
                "tier": normalized_tier
            }
        else:
            return {
                "eligible": False,
                "message": f"❌ You need {CLUB_100_COST} available picks to access Club 100. You have {picks_available}.",
                "picks_available": picks_available,
                "picks_needed": CLUB_100_COST,
                "tier": normalized_tier
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Club100] Error checking unlock status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check Club 100 status: {str(e)}"
        )


@router.get("/club-100/data")
async def get_club_100_data(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Club 100 data - real players who covered their prop lines 100% in last 4-5 games
    
    REQUIRES: User must have paid 5 daily picks to access Club 100 (locked endpoint)
    Prop lines are hidden initially and shown only after user clicks to follow/unlock (costs 1 pick each)"""
    try:
        logger.info(f"[CLUB100] User {current_user_id} accessing Club 100 data")
        
        # Verify user exists and has purchased Club 100 access
        result = await db.execute(select(User).where(User.id == current_user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            logger.error(f"[CLUB100] User {current_user_id} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # CHECK: User must have 5 available picks today (no persistent flag needed)
        # Dynamic check: do they have 5 unused picks available RIGHT NOW?
        normalized_tier = (user.subscription_tier or 'starter').lower().strip()
        tier_config = TierFeatures.get_tier_config(normalized_tier)
        if not tier_config:
            tier_config = TierFeatures.get_tier_config('starter')
        tier_name = tier_config.get('name', 'Starter') if tier_config else 'Starter'
        daily_limit = tier_config.get('predictions_per_day', 1) if tier_config else 1
        
        # Check if tier has unlimited picks
        if normalized_tier in ['pro_plus', 'elite']:
            logger.info(f"[CLUB100] {normalized_tier} tier has unlimited picks, allowing Club 100 access")
        else:
            # Count daily picks used TODAY - EXCLUDE Club 100 access picks
            from app.models.db_models import user_predictions, Prediction
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            daily_picks_stmt = select(func.count()).select_from(user_predictions).join(
                Prediction, user_predictions.c.prediction_id == Prediction.id
            ).where(
                and_(
                    user_predictions.c.user_id == current_user_id,
                    Prediction.created_at >= today_start,
                    Prediction.sport != 'club_100_access'
                )
            )
            
            daily_picks_result = await db.execute(daily_picks_stmt)
            daily_picks_used = daily_picks_result.scalar() or 0
            picks_available = daily_limit - daily_picks_used
            
            logger.info(f"[CLUB100] User {current_user_id}: used {daily_picks_used}, available {picks_available}, limit {daily_limit}")
            
            # Club 100 requires 5 available picks
            CLUB_100_COST = 5
            if picks_available < CLUB_100_COST:
                logger.warning(f"[CLUB100] User {current_user_id} denied - only {picks_available} picks available, needs {CLUB_100_COST}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"🔒 **Club 100 Access Required**\n\n"
                           f"Club 100 is an exclusive area showing elite player predictions.\n"
                           f"Access requires **{CLUB_100_COST} available daily picks**.\n\n"
                           f"_Your Plan:_ {tier_name}\n"
                           f"_Daily limit:_ {daily_limit} picks\n"
                           f"_Picks used today:_ {daily_picks_used}\n"
                           f"_Picks available:_ {picks_available}\n\n"
                           f"**Upgrade your plan or come back tomorrow with fresh picks!** 🚀"
                )
        
        logger.info(f"[CLUB100] User {current_user_id} has sufficient picks for Club 100 access: {user.email}")
        
        # Import Club100Service to get real player prop data
        from app.services.club_100_service import Club100Service
        service = Club100Service()
        
        # Get Club 100 data with unlocked status
        # Prop lines are hidden for non-unlocked picks
        club_100_data = await service.get_club_100_data_with_unlocked_status(db, current_user_id)
        
        logger.info(f"[CLUB100] Retrieved Club 100 data with unlocked picks")
        
        return {
            "success": True,
            "data": club_100_data,
            "description": "Elite players who cleared their prop lines 100% of the time in last 4-5 games. Click 'Follow' to unlock the prop line (costs 1 pick each).",
            "initial_access_cost": 5,
            "follow_cost_per_pick": 1
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CLUB100] Error getting Club 100 data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Club 100 data: {str(e)}"
        )


@router.post("/club-100/follow/{player_id}")
async def follow_club_100_pick(
    player_id: str = Path(..., description="Player ID to follow"),
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Follow/unlock a specific Club 100 pick (costs 1 daily pick)
    
    Returns the prop line for this player after unlocking"""
    try:
        logger.info(f"[CLUB100] User {current_user_id} following pick {player_id}")
        
        # Get the user
        result = await db.execute(select(User).where(User.id == current_user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            logger.error(f"[CLUB100] User {current_user_id} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Check daily picks available
        try:
            from app.models.db_models import user_predictions, Prediction
            from datetime import timezone
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
            daily_picks_stmt = select(func.count()).select_from(user_predictions).join(
                Prediction, user_predictions.c.prediction_id == Prediction.id
            ).where(
                and_(
                    user_predictions.c.user_id == current_user_id,
                    Prediction.created_at >= today_start
                )
            )
            
            daily_picks_result = await db.execute(daily_picks_stmt)
            daily_picks_used = daily_picks_result.scalar() or 0
        except Exception as e:
            logger.warning(f"Could not count daily picks for {current_user_id}: {e}")
            daily_picks_used = 0
        
        # Get tier config
        try:
            from app.models.tier_features import TierFeatures
            normalized_tier = (user.subscription_tier or 'starter').lower().strip()
            tier_config = TierFeatures.get_tier_config(normalized_tier)
            daily_limit = tier_config.get('predictions_per_day') or 999999
        except Exception as e:
            logger.warning(f"Could not get tier config: {e}")
            daily_limit = 999999
        
        daily_picks_available = daily_limit - daily_picks_used
        
        # Check if user has at least 1 pick available
        if daily_picks_available < 1:
            logger.warning(f"User {current_user_id} has insufficient picks. Have {daily_picks_available}, need 1")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient picks. You have {max(0, daily_picks_available)} picks available. Need 1 pick to follow this player."
            )
        
        # Use Club100Service to follow the pick
        from app.services.club_100_service import Club100Service
        service = Club100Service()
        
        try:
            result = await service.follow_club_100_pick(db, current_user_id, player_id)
            logger.info(f"[CLUB100] Successfully followed player {player_id} for user {current_user_id}")
            
            return {
                "success": True,
                **result,
                "daily_picks_remaining": daily_picks_available - 1
            }
            
        except ValueError as e:
            error_msg = str(e)
            if "already unlocked" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"You have already unlocked this player. Click 'Following' to view the prop line."
                )
            elif "not found" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Player not found in Club 100"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CLUB100] Error following Club 100 pick {player_id} for user {current_user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to follow Club 100 pick: {str(e)}"
        )


@router.get("/club-100/platform-metrics")
async def get_club_100_platform_metrics(
    db: AsyncSession = Depends(get_db)
):
    """Get platform-wide Club 100 metrics - aggregated stats from all users (no auth required)"""
    try:
        from sqlalchemy import select, func as sa_func
        from app.models.db_models import Prediction, user_predictions
        
        logger.info("[CLUB100] Fetching platform-wide metrics")
        
        # Get all Club 100 predictions (identified by being from the platform picks)
        # Count unique users following Club 100 predictions
        result = await db.execute(
            select(sa_func.count(sa_func.distinct(user_predictions.c.user_id)))
            .select_from(user_predictions)
        )
        total_users_following = result.scalar() or 0
        
        # Get average confidence across all predictions (as decimal 0-1, EXCLUDE Club 100 access picks)
        result = await db.execute(
            select(sa_func.avg(Prediction.confidence))
            .where(
                Prediction.confidence.isnot(None),
                Prediction.sport != 'club_100_access'
            )
        )
        avg_confidence = float(result.scalar() or 0)  # Decimal form 0-1
        
        # Get total predictions across platform (EXCLUDE Club 100 access picks)
        result = await db.execute(
            select(sa_func.count(Prediction.id))
            .where(Prediction.sport != 'club_100_access')
        )
        total_predictions = result.scalar() or 0
        
        # Calculate win rate (predictions that resolved as wins, EXCLUDE Club 100 access picks)
        result = await db.execute(
            select(sa_func.count(Prediction.id))
            .where(
                Prediction.result == 'win',
                Prediction.sport != 'club_100_access'
            )
        )
        total_wins = result.scalar() or 0
        
        # Win rate as decimal (0-1), NOT percentage
        win_rate = (total_wins / total_predictions) if total_predictions > 0 else 0.0
        
        logger.info(f"[CLUB100] Platform metrics: users={total_users_following}, predictions={total_predictions}, win_rate={win_rate*100:.1f}%, avg_confidence={avg_confidence*100:.1f}%")
        
        return {
            "success": True,
            "total_users_following": total_users_following,
            "total_predictions": total_predictions,
            "win_rate": round(win_rate, 4),  # Decimal form 0-1
            "avg_confidence": round(avg_confidence, 4),  # Decimal form 0-1
            "description": "Aggregated metrics from all platform users"
        }
    except Exception as e:
        logger.error(f"[CLUB100] Error getting platform metrics: {str(e)}", exc_info=True)
        # Return defaults instead of error, so frontend doesn't break
        return {
            "success": False,
            "total_users_following": 0,
            "total_predictions": 0,
            "win_rate": 0.0,
            "avg_confidence": 0.0,
            "description": "Could not fetch metrics - using defaults"
        }


# ====== TEST ENDPOINT (No Auth Required) ======
@router.get("/test/player-props")
async def test_player_props(
    sport_key: str = Query("basketball_nba", description="Sport key"),
    event_id: str = Query("test123", description="Event ID"),
    db: AsyncSession = Depends(get_db)
):
    """TEST ENDPOINT - Get player props without authentication (for debugging)"""
    try:
        logger.info(f"[TEST_PROPS] Getting test player props for {sport_key}/{event_id}")
        
        # Try ESPN service
        props = None
        try:
            props = await get_espn_service().get_player_props(sport_key, event_id)
            logger.info(f"[TEST_PROPS] ESPN returned {len(props)} props")
        except Exception as e:
            logger.warning(f"[TEST_PROPS] ESPN failed: {e}. Using fallback...")
        
        # NO MOCK DATA - if ESPN unavailable, return empty
        if not props:
            logger.info(f"[TEST_PROPS] ESPN unavailable - returning empty (NO MOCK DATA)")
        
        # Add sport/league if missing
        for prop in props:
            if 'sport' not in prop or not prop['sport']:
                prop['sport'] = 'NBA' if 'basketball' in sport_key else \
                               'NFL' if 'football' in sport_key else \
                               'NHL' if 'hockey' in sport_key else \
                               'MLB' if 'baseball' in sport_key else \
                               'Soccer' if 'soccer' in sport_key else 'Unknown'
            if 'league' not in prop or not prop['league']:
                prop['league'] = sport_key.split('_')[-1].upper() if '_' in sport_key else sport_key.upper()
        
        logger.info(f"[TEST_PROPS] Returning {len(props)} total props")
        return props
        
    except Exception as e:
        logger.error(f"[TEST_PROPS] Error: {e}", exc_info=True)
        return {"error": str(e), "count": 0}


# ====== DATA POPULATION ENDPOINTS ======

class DataSyncRequest(BaseModel):
    """Request model for data synchronization"""
    sport: str  # nba, nfl, nhl, mlb, soccer
    days_back: int = 30
    limit: int = 100

class DataSyncResponse(BaseModel):
    """Response model for data synchronization"""
    success: bool
    sport: str
    games_processed: int
    player_logs_created: int
    players_synced: int
    error: Optional[str] = None


@router.post("/data/sync-game-logs", response_model=DataSyncResponse)
async def sync_game_logs(
    request: DataSyncRequest,
    current_user: Optional[str] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger synchronization of player game logs for a sport.
    Fetches historical game data from ESPN and populates player_game_logs table.
    
    Parameters:
    - sport: Sport key (nba, nfl, nhl, mlb, soccer)
    - days_back: Number of days back to fetch (default: 30)
    - limit: Max games to fetch (default: 100)
    
    Requires authentication (admin recommended).
    """
    try:
        # Check if user is authorized (you may want to add admin check here)
        logger.info(f"[SYNC] User {current_user} requesting data sync for {request.sport}")
        
        # Import here to avoid circular imports
        from app.services.player_data_service import PlayerDataService
        
        service = PlayerDataService(db)
        try:
            result = await service.sync_historical_game_logs(
                sport=request.sport,
                days_back=request.days_back,
                limit=request.limit
            )
            
            # Commit changes to database
            await service.commit_changes()
            
            logger.info(f"[SYNC] Completed sync for {request.sport}: {result}")
            
            return DataSyncResponse(
                success=result.get("success", False),
                sport=result.get("sport", request.sport),
                games_processed=result.get("games_processed", 0),
                player_logs_created=result.get("player_logs_created", 0),
                players_synced=result.get("players_synced", 0),
                error=result.get("error")
            )
        finally:
            await service.close()
            
    except Exception as e:
        logger.error(f"[SYNC] Error syncing game logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.get("/data/sync-status")
async def get_sync_status(
    sport: Optional[str] = Query(None, description="Filter by sport"),
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get synchronization status for player game logs.
    Shows how many players and game logs are in the database.
    """
    try:
        from app.models.prediction_records import PlayerRecord, PlayerGameLog
        
        # Get player count
        stmt = select(func.count(PlayerRecord.id))
        if sport:
            stmt = stmt.where(PlayerRecord.sport_key.contains(sport))
        
        result = await db.execute(stmt)
        player_count = result.scalar() or 0
        
        # Get game log count
        stmt = select(func.count(PlayerGameLog.id))
        if sport:
            stmt = stmt.where(PlayerGameLog.sport_key.contains(sport))
        
        result = await db.execute(stmt)
        game_log_count = result.scalar() or 0
        
        # Get sports with data
        stmt = select(func.distinct(PlayerRecord.sport_key))
        result = await db.execute(stmt)
        sports_with_data = [row[0] for row in result.fetchall() if row[0]]
        
        logger.info(f"[SYNC_STATUS] Players: {player_count}, Game Logs: {game_log_count}")
        
        return {
            "total_players": player_count,
            "total_game_logs": game_log_count,
            "sports_synced": list(set(sports_with_data)),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"[SYNC_STATUS] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


@router.get("/player/{player_id}/game-logs")
async def get_player_game_logs(
    player_id: str = Path(..., description="Player ID"),
    limit: int = Query(10, ge=1, le=100, description="Max games to return"),
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent game logs for a specific player.
    Used by Club 100 and other features that need player performance history.
    """
    try:
        from app.models.prediction_records import PlayerGameLog, PlayerRecord
        
        # First, get the player
        player_stmt = select(PlayerRecord).where(PlayerRecord.id == player_id)
        player_result = await db.execute(player_stmt)
        player = player_result.scalars().first()
        
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Player not found: {player_id}"
            )
        
        # Get game logs
        stmt = (
            select(PlayerGameLog)
            .where(PlayerGameLog.player_id == player.id)
            .order_by(PlayerGameLog.date.desc())
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        game_logs = result.scalars().all()
        
        return {
            "player": {
                "id": player.id,
                "name": player.name,
                "sport": player.sport_key,
                "team": player.team_key,
            },
            "game_logs": [
                {
                    "date": game.date.isoformat(),
                    "opponent": game.opponent,
                    "home_away": game.home_away,
                    "stats": game.stats,
                    "team_score": game.team_score,
                    "opponent_score": game.opponent_score,
                    "event_id": game.event_id,
                }
                for game in game_logs
            ],
            "total_games": len(game_logs),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PLAYER_LOGS] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get game logs: {str(e)}"
        )


@router.post("/data/populate-demo-data")
async def populate_demo_data(
    sports: List[str] = Body(default=["nba", "nfl"], description="List of sports to populate"),
    current_user: Optional[str] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Populate demo/sample game logs for testing.
    This endpoint syncs data for multiple sports at once.
    
    Sports supported: nba, nfl, nhl, mlb, soccer
    """
    try:
        from app.services.player_data_service import PlayerDataService
        
        logger.info(f"[DEMO_DATA] Populating demo data for sports: {sports}")
        
        results = {}
        service = PlayerDataService(db)
        
        try:
            for sport in sports:
                logger.info(f"[DEMO_DATA] Syncing {sport}...")
                result = await service.sync_historical_game_logs(
                    sport=sport,
                    days_back=14,  # Only last 2 weeks for demo
                    limit=50       # Limit games to keep demo data manageable
                )
                results[sport] = result
            
            # Commit all changes
            await service.commit_changes()
            
            logger.info(f"[DEMO_DATA] Demo data population complete: {results}")
            
            return {
                "success": True,
                "message": f"Demo data populated for {len(sports)} sports",
                "results": results,
            }
            
        finally:
            await service.close()
            
    except Exception as e:
        logger.error(f"[DEMO_DATA] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demo data population failed: {str(e)}"
        )
