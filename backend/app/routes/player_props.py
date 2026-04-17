
# Lazy-initialized services to prevent import hangs
_auth_service = None

def get_auth_service():
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


"""
Player Props API Routes
Endpoints for player prop predictions
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth_service import AuthService
from app.models.db_models import User
from app.services.player_props_service import PlayerPropsService
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/events", tags=["player_props"])
# Lazy-loaded
auth_service = None

@router.get("/{event_id}/player-props")
async def get_player_props(
    event_id: str,
    sport_key: str = Query(..., description="nba, nfl, mlb, nhl, soccer"),
    home_team: str = Query(...),
    away_team: str = Query(...),
    stat_type: Optional[str] = Query(None, description="Filter by stat type: points, rebounds, etc"),
    min_confidence: float = Query(0.55, ge=0.5, le=1.0),
    current_user_id: str = Depends(lambda: get_auth_service().get_current_user()),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all available player prop predictions for a game
    
    Returns list of player props with:
    - player_name: Player name
    - stat_type: Type of stat (points, rebounds, assists, etc)
    - predicted_line: Predicted over/under line
    - over_confidence: Confidence in over (0.0-1.0)
    - under_confidence: Confidence in under
    - reasoning: Why this prediction was made
    - season_avg: Player's season average for this stat
    - last_5_avg: Average over last 5 games
    """
    service = PlayerPropsService(db)
    
    props = await service.generate_player_prop_predictions(
        event_id=event_id,
        sport_key=sport_key,
        home_team=home_team,
        away_team=away_team
    )
    
    # Filter by stat type if specified
    if stat_type:
        props = [p for p in props if p['stat_type'] == stat_type]
    
    # Filter by minimum confidence
    props = [
        p for p in props
        if max(p['over_confidence'], p['under_confidence']) >= min_confidence
    ]
    
    return {
        'event_id': event_id,
        'sport_key': sport_key,
        'player_props': props,
        'total': len(props)
    }

@router.get("/{event_id}/player-props/{player_id}")
async def get_player_specific_props(
    event_id: str,
    player_id: str,
    sport_key: str = Query(...),
    current_user_id: str = Depends(lambda: get_auth_service().get_current_user()),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed prop predictions for a specific player in a game
    
    Returns:
    {
        'player_id': 'abc123',
        'player_name': 'LeBron James',
        'position': 'SF',
        'stats': {
            'points': {
                'line': 24.5,
                'over_confidence': 0.65,
                'reasoning': '...',
                'season_avg': 25.2,
                'last_5_avg': 26.1
            },
            'rebounds': {...},
            'assists': {...}
        }
    }
    """
    service = PlayerPropsService(db)
    
    # Get multiple stats for this player
    # In production, would fetch event details first
    props = await service.generate_player_prop_predictions(
        event_id=event_id,
        sport_key=sport_key,
        home_team='',  # Would be fetched from ESPN
        away_team=''
    )
    
    # Filter to this player
    player_props = [p for p in props if p['player_id'] == player_id]
    
    if not player_props:
        return {'error': 'No props for this player'}
    
    # Reorganize by stat type
    stats_by_type = {}
    for prop in player_props:
        stat_type = prop['stat_type']
        stats_by_type[stat_type] = {
            'line': prop['predicted_line'],
            'over_confidence': prop['over_confidence'],
            'under_confidence': prop['under_confidence'],
            'reasoning': prop['reasoning'],
            'season_avg': prop['season_avg'],
            'last_5_avg': prop['last_5_avg']
        }
    
    return {
        'player_id': player_id,
        'player_name': player_props[0]['player_name'],
        'position': player_props[0].get('position'),
        'stats': stats_by_type
    }

@router.post("/{event_id}/player-props/{player_id}/select")
async def select_player_prop(
    event_id: str,
    player_id: str,
    stat_type: str = Query(...),
    side: str = Query(..., description="over or under"),
    current_user_id: str = Depends(lambda: get_auth_service().get_current_user()),
    db: AsyncSession = Depends(get_db)
):
    """
    User selects a player prop (over or under)
    
    Records the prediction in user history
    """
    from app.services.prediction_history_service import PredictionHistoryService
    
    history_service = PredictionHistoryService(db)
    
    # This would be called after user clicks over/under
    # Record prediction in history
    pred_data = {
        'matchup': f'{player_id} {stat_type}',
        'prediction_type': 'player_props',
        'prediction': f'{stat_type.upper()} {side.upper()}',
        'player_name': player_id,
        'stat_type': stat_type,
        'confidence': 0.58,  # Would come from props service
        'reasoning': []
    }
    
    prediction_id = await history_service.record_prediction(
        user_id=current_user_id,
        sport_key='nba',  # Would detect from event
        event_id=event_id,
        prediction_data=pred_data
    )
    
    return {
        'prediction_id': prediction_id,
        'status': 'recorded',
        'event_id': event_id,
        'player_id': player_id
    }

@router.get("/player/{player_id}/season-stats")
async def get_player_season_stats(
    player_id: str,
    sport_key: str = Query(...),
    current_user_id: str = Depends(lambda: get_auth_service().get_current_user()),
    db: AsyncSession = Depends(get_db)
):
    """
    Get season statistics for a player
    """
    from app.models.prediction_records import PlayerRecord, PlayerSeasonStats
    from sqlalchemy import select
    
    # Get player
    result = await db.execute(
        select(PlayerRecord).where(PlayerRecord.id == player_id)
    )
    player = result.scalars().first()
    
    if not player:
        return {'error': 'Player not found'}
    
    # Get season stats
    current_year = 2026
    result = await db.execute(
        select(PlayerSeasonStats).where(
            PlayerSeasonStats.player_id == player_id,
            PlayerSeasonStats.season == current_year
        )
    )
    season_stats = result.scalars().first()
    
    if not season_stats:
        return {'error': 'No season stats for this player'}
    
    # Return relevant stats based on sport
    stats_dict = {
        'player_name': player.name,
        'sport_key': sport_key,
        'season': season_stats.season,
        'games_played': season_stats.games_played,
        'games_started': season_stats.games_started
    }
    
    if sport_key == 'nba':
        stats_dict.update({
            'ppg': season_stats.ppg,
            'rpg': season_stats.rpg,
            'apg': season_stats.apg,
            'spg': season_stats.spg,
            'bpg': season_stats.bpg,
            'fg_percent': season_stats.fg_percent,
            'three_pt_percent': season_stats.three_pt_percent,
            'ft_percent': season_stats.ft_percent
        })
    elif sport_key == 'nfl':
        stats_dict.update({
            'pass_yards_per_game': season_stats.pass_yards_per_game,
            'pass_tds': season_stats.pass_tds,
            'rush_yards_per_game': season_stats.rush_yards_per_game,
            'receiving_yards_per_game': season_stats.receiving_yards_per_game
        })
    elif sport_key == 'mlb':
        stats_dict.update({
            'batting_avg': season_stats.batting_avg,
            'home_runs': season_stats.home_runs,
            'rbi': season_stats.rbi,
            'strikeouts': season_stats.strikeouts
        })
    
    return stats_dict

@router.get("/player/{player_id}/game-logs")
async def get_player_game_logs(
    player_id: str,
    limit: int = Query(10, ge=1, le=50),
    current_user_id: str = Depends(lambda: get_auth_service().get_current_user()),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent game logs for a player
    """
    from app.models.prediction_records import PlayerGameLog
    from sqlalchemy import select, desc
    
    result = await db.execute(
        select(PlayerGameLog).where(
            PlayerGameLog.player_id == player_id
        ).order_by(desc(PlayerGameLog.date)).limit(limit)
    )
    
    logs = result.scalars().all()
    
    return {
        'player_id': player_id,
        'game_logs': [
            {
                'date': log.date.isoformat(),
                'event_id': log.event_id,
                'stats': log.stats
            }
            for log in reversed(logs)  # Chronological order
        ]
    }

@router.get("/props/trending")
async def get_trending_props(
    sport_key: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
    current_user_id: str = Depends(lambda: get_auth_service().get_current_user()),
    db: AsyncSession = Depends(get_db)
):
    """
    Get trending player props across all games
    Trending = High confidence and nearing game time
    """
    # Would query all upcoming games and return top trending props
    return {
        'sport_key': sport_key,
        'trending_props': [],
        'last_updated': '2026-03-07T12:00:00'
    }

@router.get("/props/recommendations")
async def get_prop_recommendations(
    sport_key: str = Query(...),
    current_user_id: str = Depends(lambda: get_auth_service().get_current_user()),
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI recommendations for props based on user's track record
    """
    from app.services.prediction_history_service import PredictionHistoryService
    
    history_service = PredictionHistoryService(db)
    
    # Get user's accuracy in this sport
    sport_stats = await history_service.get_user_stats_by_sport(current_user.id)
    sport_data = sport_stats.get(sport_key, {})
    
    return {
        'sport_key': sport_key,
        'user_accuracy_this_sport': sport_data.get('win_rate', 0.0),
        'recommended_props': [],
        'recommendation_basis': 'high_confidence_for_user_strong_sports'
    }
