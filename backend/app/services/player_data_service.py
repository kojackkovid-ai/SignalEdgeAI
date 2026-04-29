"""
Player Data Service
Fetches and populates player game logs with historical data from ESPN
"""

import httpx
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, insert, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
import asyncio
import uuid

from app.models.prediction_records import PlayerRecord, PlayerGameLog

logger = logging.getLogger(__name__)


class PlayerDataService:
    """
    Service to fetch and populate player game logs with historical data.
    Supports NBA, NFL, NHL, MLB, and Soccer.
    """
    
    BASE_URL = "https://site.api.espn.com/apis/site/v2"
    
    SPORT_MAPPING = {
        "nba": {
            "api_path": "basketball/nba",
            "stats_map": {
                "points": "points",
                "rebounds": "rebounds",
                "assists": "assists",
                "steals": "steals",
                "blocks": "blocks",
                "field_goal_pct": "fieldGoalPct",
                "three_point_pct": "threePointPct",
                "free_throw_pct": "freeThrowPct",
            }
        },
        "nfl": {
            "api_path": "football/nfl",
            "stats_map": {
                "pass_yards": "passingYards",
                "pass_touchdowns": "passingTouchdowns",
                "interceptions": "interceptions",
                "rush_yards": "rushingYards",
                "rush_touchdowns": "rushingTouchdowns",
                "receptions": "receptions",
                "receiving_yards": "receivingYards",
                "receiving_touchdowns": "receivingTouchdowns",
            }
        },
        "nhl": {
            "api_path": "hockey/nhl",
            "stats_map": {
                "goals": "goals",
                "assists": "assists",
                "shots": "shotsOnGoal",
                "blocks": "blocks",
                "hits": "hits",
                "plus_minus": "plusMinus",
            }
        },
        "mlb": {
            "api_path": "baseball/mlb",
            "stats_map": {
                "hits": "hits",
                "home_runs": "homeRuns",
                "rbis": "runsBattedIn",
                "runs": "runs",
                "stolen_bases": "stolenBases",
                "batting_avg": "battingAverage",
            }
        },
        "soccer": {
            "api_path": "soccer/league-name",  # Will be dynamically set
            "stats_map": {
                "goals": "goals",
                "assists": "assists",
                "shots": "shots",
                "tackles": "tackles",
                "passes": "passes",
            }
        },
    }
    
    def __init__(self, db: AsyncSession):
        """Initialize service with database session"""
        self.db = db
        self.client = httpx.AsyncClient(timeout=15.0)
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def sync_historical_game_logs(
        self, 
        sport: str, 
        days_back: int = 30,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Fetch and populate game logs for a sport from past N days.
        
        Args:
            sport: Sport key (nba, nfl, nhl, mlb, soccer)
            days_back: Number of days to fetch historical data for
            limit: Max games to fetch
            
        Returns:
            Dict with stats about populated data
        """
        logger.info(f"Starting sync of {sport} game logs for last {days_back} days")
        
        sport_key = sport.lower()
        if sport_key not in self.SPORT_MAPPING:
            logger.error(f"Unsupported sport: {sport}")
            return {"success": False, "error": f"Unsupported sport: {sport}"}
        
        try:
            # Get scoreboard data for the period
            games_data = await self._fetch_games(sport_key, days_back, limit)
            
            if not games_data:
                logger.warning(f"No games found for {sport} in last {days_back} days")
                return {
                    "success": True,
                    "sport": sport,
                    "games_processed": 0,
                    "player_logs_created": 0,
                    "players_synced": 0,
                }
            
            # Process games and extract player stats
            result = await self._process_games(sport_key, games_data)
            
            logger.info(
                f"Sync complete for {sport}: "
                f"{result['games_processed']} games, "
                f"{result['player_logs_created']} player logs, "
                f"{result['players_synced']} players"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error syncing {sport} game logs: {e}", exc_info=True)
            return {"success": False, "error": str(e), "sport": sport}
    
    async def _fetch_games(
        self, 
        sport: str, 
        days_back: int,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch games from ESPN API for the past N days"""
        sport_mapping = self.SPORT_MAPPING.get(sport)
        if not sport_mapping:
            return []
        
        api_path = sport_mapping["api_path"]
        url = f"{self.BASE_URL}/sports/{api_path}/scoreboard"
        
        # We'll make multiple requests for different dates if needed
        all_games = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        current_date = start_date
        while current_date <= end_date:
            try:
                # Format: YYYYMMDD
                date_str = current_date.strftime("%Y%m%d")
                
                response = await self.client.get(url, params={"dates": date_str})
                response.raise_for_status()
                
                data = response.json()
                events = data.get("events", [])
                
                # Filter for completed games only
                for event in events:
                    if event.get("status", {}).get("type", {}).get("completed"):
                        all_games.append(event)
                
                if len(all_games) >= limit:
                    break
                    
                current_date += timedelta(days=1)
                
            except Exception as e:
                logger.warning(f"Error fetching games for {date_str}: {e}")
                current_date += timedelta(days=1)
                continue
        
        return all_games[:limit]
    
    async def _process_games(
        self, 
        sport: str, 
        games: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process games and create/update player game logs"""
        games_processed = 0
        player_logs_created = 0
        players_synced = 0
        players_created = set()
        
        sport_mapping = self.SPORT_MAPPING.get(sport)
        if not sport_mapping:
            return {
                "success": False,
                "error": f"Unknown sport: {sport}",
                "games_processed": 0,
                "player_logs_created": 0,
                "players_synced": 0,
            }
        
        for game in games:
            try:
                game_data = await self._extract_game_data(sport, game)
                if not game_data:
                    continue
                
                # Process player stats from this game
                for player_stat in game_data.get("player_stats", []):
                    # Get or create player
                    player = await self._get_or_create_player(
                        sport,
                        player_stat["name"],
                        player_stat.get("player_id"),
                        player_stat.get("team")
                    )
                    
                    if player["created"]:
                        players_created.add(player["id"])
                    
                    # Create game log entry
                    log_created = await self._create_game_log(
                        player_id=player["id"],
                        event_id=game_data["event_id"],
                        sport_key=game_data["sport_key"],
                        date=game_data["date"],
                        stats=player_stat.get("stats", {}),
                        opponent=player_stat.get("opponent"),
                        home_away=player_stat.get("home_away"),
                        team_score=player_stat.get("team_score") if player_stat.get("team_score") is not None else game_data.get("team_score"),
                        opponent_score=player_stat.get("opponent_score") if player_stat.get("opponent_score") is not None else game_data.get("opponent_score"),
                    )
                    
                    if log_created:
                        player_logs_created += 1
                
                games_processed += 1
                
            except Exception as e:
                logger.error(f"Error processing game {game.get('id')}: {e}")
                continue
        
        players_synced = len(players_created)
        
        return {
            "success": True,
            "sport": sport,
            "games_processed": games_processed,
            "player_logs_created": player_logs_created,
            "players_synced": players_synced,
        }
    
    async def _extract_game_data(
        self, 
        sport: str, 
        game: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Extract relevant game data and player stats from ESPN game object"""
        try:
            event_id = game.get("id")
            date_str = game.get("date")
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            
            competitions = game.get("competitions", [])
            if not competitions:
                return None
            
            competition = competitions[0]
            competitors = competition.get("competitors", [])
            
            # Get home and away teams
            home_team = next((c for c in competitors if c.get("homeAway") == "home"), None)
            away_team = next((c for c in competitors if c.get("homeAway") == "away"), None)
            
            if not home_team or not away_team:
                return None
            
            home_team_name = home_team.get("team", {}).get("displayName", "")
            away_team_name = away_team.get("team", {}).get("displayName", "")
            home_score = int(home_team.get("score", 0))
            away_score = int(away_team.get("score", 0))
            
            # Extract player stats from each team
            player_stats = []

            player_stats.extend(
                self._extract_player_stats_from_team(
                    home_team,
                    sport,
                    home_team_name,
                    away_team_name,
                    "home",
                    home_score,
                    away_score,
                )
            )

            player_stats.extend(
                self._extract_player_stats_from_team(
                    away_team,
                    sport,
                    away_team_name,
                    home_team_name,
                    "away",
                    away_score,
                    home_score,
                )
            )

            return {
                "event_id": event_id,
                "date": date,
                "sport_key": self.SPORT_MAPPING[sport]["api_path"],
                "player_stats": player_stats,
                "team_score": None,
                "opponent_score": None,
            }
            
        except Exception as e:
            logger.error(f"Error extracting game data: {e}")
            return None
    
    def _extract_player_stats_from_team(
        self,
        team: Dict[str, Any],
        sport: str,
        team_name: str,
        opponent_name: str,
        home_away: str,
        team_score: Optional[int] = None,
        opponent_score: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Extract player statistics from a team's competition data"""
        players_by_id = {}
        
        # ESPN provides a list of leader categories, each with its own leaders array
        leader_categories = team.get("leaders", [])
        
        for category in leader_categories:
            category_name = category.get("name") or category.get("displayName")
            if not category_name:
                continue
            stat_key = category_name.lower().replace(" ", "_")
            for leader in category.get("leaders", []):
                athlete = leader.get("athlete") or {}
                if not athlete:
                    continue
                player_id = athlete.get("id")
                player_name = athlete.get("fullName") or athlete.get("displayName")
                if not player_name:
                    continue
                stat_value = leader.get("value", leader.get("displayValue"))
                try:
                    stat_value = float(stat_value)
                except (ValueError, TypeError):
                    pass
                key = player_id or player_name
                if key not in players_by_id:
                    players_by_id[key] = {
                        "name": player_name,
                        "player_id": player_id,
                        "team": team_name,
                        "opponent": opponent_name,
                        "home_away": home_away,
                        "team_score": team_score,
                        "opponent_score": opponent_score,
                        "stats": {},
                    }
                players_by_id[key]["stats"][stat_key] = stat_value
        
        # If there are no leader categories, try direct athlete stats fallback
        if not players_by_id:
            athletes = team.get("athletes", [])
            for athlete in athletes:
                name = athlete.get("fullName") or athlete.get("displayName")
                player_id = athlete.get("id")
                if not name:
                    continue
                stats = {}
                for stat in athlete.get("stats", []):
                    stat_type = stat.get("name", "").lower().replace(" ", "_")
                    stat_value = stat.get("displayValue", stat.get("value", 0))
                    try:
                        stats[stat_type] = float(stat_value)
                    except (ValueError, TypeError):
                        stats[stat_type] = stat_value
                players_by_id[player_id or name] = {
                    "name": name,
                    "player_id": player_id,
                    "team": team_name,
                    "opponent": opponent_name,
                    "home_away": home_away,
                    "team_score": team_score,
                    "opponent_score": opponent_score,
                    "stats": stats if stats else {"games_played": 1},
                }
        
        return list(players_by_id.values())
    
    async def _get_or_create_player(
        self,
        sport: str,
        player_name: str,
        player_id: Optional[str] = None,
        team: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get existing player or create new one"""
        try:
            # Try to find existing player
            sport_key = self.SPORT_MAPPING.get(sport, {}).get("api_path", sport)
            
            stmt = select(PlayerRecord).where(
                and_(
                    PlayerRecord.name == player_name,
                    PlayerRecord.sport_key == sport_key,
                    PlayerRecord.team_key == team if team else True
                )
            )
            
            result = await self.db.execute(stmt)
            existing_player = result.scalars().first()
            
            if existing_player:
                return {
                    "id": existing_player.id,
                    "created": False,
                }
            
            # Create new player
            new_player_id = str(uuid.uuid4())
            new_player = PlayerRecord(
                id=new_player_id,
                name=player_name,
                team_key=team,
                sport_key=sport_key,
                position=None,  # Extract from data if available
            )
            
            # Set external IDs based on sport
            if sport.lower() == "nba" and player_id:
                new_player.nba_id = player_id
            elif sport.lower() == "nfl" and player_id:
                new_player.nfl_id = player_id
            elif sport.lower() == "mlb" and player_id:
                new_player.mlb_id = player_id
            elif sport.lower() == "nhl" and player_id:
                new_player.nhl_id = player_id
            
            self.db.add(new_player)
            await self.db.flush()
            
            logger.info(f"Created new player: {player_name} ({sport_key})")
            
            return {
                "id": new_player_id,
                "created": True,
            }
            
        except Exception as e:
            logger.error(f"Error getting/creating player {player_name}: {e}")
            # Return a UUID to continue processing
            return {
                "id": str(uuid.uuid4()),
                "created": False,
            }
    
    async def _create_game_log(
        self,
        player_id: str,
        event_id: str,
        sport_key: str,
        date: datetime,
        stats: Dict[str, Any],
        opponent: Optional[str] = None,
        home_away: Optional[str] = None,
        team_score: Optional[int] = None,
        opponent_score: Optional[int] = None,
    ) -> bool:
        """Create a new game log entry"""
        try:
            # Check if this game log already exists
            stmt = select(PlayerGameLog).where(
                and_(
                    PlayerGameLog.player_id == player_id,
                    PlayerGameLog.event_id == event_id,
                )
            )
            
            result = await self.db.execute(stmt)
            existing = result.scalars().first()
            
            if existing:
                # Update existing log
                existing.stats = stats
                existing.opponent = opponent
                existing.home_away = home_away
                existing.team_score = team_score
                existing.opponent_score = opponent_score
                existing.updated_at = datetime.utcnow()
                
                await self.db.flush()
                return False  # Not a new creation
            
            # Create new game log
            game_log = PlayerGameLog(
                id=str(uuid.uuid4()),
                player_id=player_id,
                event_id=event_id,
                sport_key=sport_key,
                date=date,
                stats=stats,
                opponent=opponent,
                home_away=home_away,
                team_score=team_score,
                opponent_score=opponent_score,
            )
            
            self.db.add(game_log)
            await self.db.flush()
            
            return True  # New creation
            
        except Exception as e:
            logger.error(f"Error creating game log: {e}")
            return False
    
    async def get_player_last_games(
        self,
        player_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent games for a player"""
        try:
            stmt = (
                select(PlayerGameLog)
                .where(PlayerGameLog.player_id == player_id)
                .order_by(PlayerGameLog.date.desc())
                .limit(limit)
            )
            
            result = await self.db.execute(stmt)
            games = result.scalars().all()
            
            return [
                {
                    "date": game.date,
                    "opponent": game.opponent,
                    "stats": game.stats,
                    "team_score": game.team_score,
                    "opponent_score": game.opponent_score,
                }
                for game in games
            ]
            
        except Exception as e:
            logger.error(f"Error getting player games: {e}")
            return []

    async def commit_changes(self):
        """Commit all database changes"""
        try:
            await self.db.commit()
            logger.info("Database changes committed successfully")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error committing changes: {e}")
            raise
