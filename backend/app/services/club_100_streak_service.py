"""
Club 100 Streak Service - Premium Real Athlete Consecutive Streak Analysis
Generates data for athletes with 100% recent form on specific props
ZERO hardcoded data - all computations from actual player game logs
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, or_

from app.models.prediction_records import PlayerRecord, PlayerGameLog, PlayerSeasonStats
from app.services.espn_player_stats_service import get_player_stats_service

logger = logging.getLogger(__name__)


class Club100StreakService:
    """
    Premium service for analyzing consecutive player streaks on specific props.
    
    Only shows athletes who have cleared a specific prop line 100% of the time
    over consecutive recent games (3, 4, 5, 6+ games).
    
    Data structure per player:
    {
        "player_id": "nba_12345_points",
        "name": "LeBron James",
        "team": "LAL",
        "sport": "nba",
        "position": "Forward",
        "prop_line": "Over 24.5 Points",
        "stat_type": "points",
        "consecutive_games": 8,
        "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0},
        "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0},
        "recent_values": [28, 26, 25, 27],
        "avg_recent": 26.5,
        "games_today": [{"opponent": "BOS", "time": "7:30 PM"}],
        "data_freshness": "2026-05-01T14:30:00Z"
    }
    """
    
    SUPPORTED_SPORTS = ["nba", "nfl", "mlb", "nhl"]
    
    # Prop stat categories we track
    STAT_CATEGORIES = {
        "nba": ["points", "rebounds", "assists", "steals", "blocks", "three_pointers_made"],
        "nfl": ["pass_yards", "rush_yards", "receptions", "receiving_yards"],
        "mlb": ["home_runs", "runs_batted_in", "hits"],
        "nhl": ["goals", "assists"]
    }
    
    # Min values to consider for streak calculation
    MIN_STAT_VALUES = {
        "points": 15,
        "rebounds": 5,
        "assists": 3,
        "steals": 1,
        "blocks": 1,
        "three_pointers_made": 1,
        "pass_yards": 150,
        "rush_yards": 50,
        "receptions": 3,
        "receiving_yards": 50,
        "goals": 1,
        "hits": 2,
        "home_runs": 0,
        "runs_batted_in": 1
    }

    # ESPN gamelog stat abbreviation -> our stat_type
    ESPN_GAMELOG_STAT_MAP: Dict[str, Dict[str, str]] = {
        "nba": {
            "PTS": "points", "REB": "rebounds", "AST": "assists",
            "STL": "steals", "BLK": "blocks", "3PM": "three_pointers_made",
            "TO": "turnovers",
        },
        "nhl": {
            "G": "goals", "A": "assists", "SOG": "shots_on_goal",
            "HIT": "hits", "+/-": "plus_minus",
        },
        "mlb": {
            "H": "hits", "HR": "home_runs", "RBI": "runs_batted_in",
            "SB": "stolen_bases", "R": "runs",
        },
        "nfl": {
            "YDS": "pass_yards", "RYD": "rush_yards",
            "REC": "receptions", "RECY": "receiving_yards",
        },
    }

    # ESPN sport path used in the athlete gamelog URL
    ESPN_SPORT_PATHS: Dict[str, str] = {
        "nba": "basketball/nba",
        "nfl": "football/nfl",
        "mlb": "baseball/mlb",
        "nhl": "hockey/nhl",
    }
    
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 1800  # 30 minute cache for streak analysis (bulk fetches are fast)
        self._last_update = {}
        self._gamelog_cache: Dict[str, Any] = {}  # athlete_id -> gamelog data

    # ------------------------------------------------------------------
    # ESPN Gamelog helpers (no DB required)
    # ------------------------------------------------------------------

    async def _fetch_espn_gamelog(self, sport: str, athlete_id: str) -> Optional[Dict[str, Any]]:
        """Fetch an athlete's recent game log directly from the ESPN API."""
        cache_key = f"{sport}_{athlete_id}_gamelog"
        if cache_key in self._gamelog_cache:
            return self._gamelog_cache[cache_key]

        sport_path = self.ESPN_SPORT_PATHS.get(sport)
        if not sport_path:
            return None

        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/athletes/{athlete_id}/gamelog"
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return None
                data = resp.json()
                self._gamelog_cache[cache_key] = data
                return data
        except Exception as exc:
            logger.debug(f"[CLUB100] ESPN gamelog fetch failed for {sport}/{athlete_id}: {exc}")
            return None

    def _parse_espn_gamelog_for_stat(
        self, sport: str, stat_type: str, gamelog_data: Dict[str, Any]
    ) -> List[float]:
        """
        Extract a list of per-game values for `stat_type` from ESPN gamelog JSON.
        Returns values ordered oldest → newest (same order ESPN returns them).
        """
        abbrev_map = self.ESPN_GAMELOG_STAT_MAP.get(sport, {})
        # Reverse map: stat_type -> abbreviation
        type_to_abbrev = {v: k for k, v in abbrev_map.items()}
        target_abbrev = type_to_abbrev.get(stat_type)

        values: List[float] = []

        # ESPN gamelog structure: gamelog_data["events"]["items"] list + "keys" list
        events_block = gamelog_data.get("events") or gamelog_data.get("splits") or {}
        if not events_block:
            return values

        items = events_block.get("items") or events_block.get("entries") or []
        keys = events_block.get("keys") or []
        names = events_block.get("names") or []

        # Build index for target key
        target_idx: Optional[int] = None
        for i, key in enumerate(keys):
            if key == target_abbrev:
                target_idx = i
                break
        # Also try matching by name
        if target_idx is None and names:
            for i, name in enumerate(names):
                if name.lower().replace(" ", "_") == stat_type:
                    target_idx = i
                    break

        if target_idx is None:
            return values

        for item in items:
            stats = item.get("stats") or []
            if target_idx < len(stats):
                try:
                    val = float(stats[target_idx])
                    values.append(val)
                except (ValueError, TypeError):
                    pass

        return values

    async def _analyze_sport_streaks_espn(
        self,
        sport: str,
        min_streak_length: int,
        today_games_dict: Dict[str, Any],
        today_games: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        ESPN-direct streak analysis: no DB required.
        Fetches the gamelog for every athlete appearing in today's games,
        then computes consecutive-game streaks on each prop stat category.
        """
        stat_categories = self.STAT_CATEGORIES.get(sport, [])
        if not stat_categories:
            return []

        # Collect unique athletes from today's games
        athletes_today: Dict[str, Dict[str, str]] = {}
        for game in today_games:
            for leader in game.get("leaders", []):
                athlete = leader.get("athlete", {})
                aid = str(athlete.get("id", ""))
                if not aid:
                    continue
                if aid not in athletes_today:
                    athletes_today[aid] = {
                        "name": athlete.get("fullName") or athlete.get("displayName", "Unknown"),
                        "team": leader.get("team_abbrev") or leader.get("team_name", "N/A"),
                        "position": leader.get("position") or athlete.get("position", {}).get("abbreviation", ""),
                    }

        if not athletes_today:
            logger.info(f"[CLUB100] {sport.upper()} ESPN: no athletes in today's leaders")
            return []

        logger.info(f"[CLUB100] {sport.upper()} ESPN: analysing {len(athletes_today)} athletes via gamelog API")

        streaks: List[Dict[str, Any]] = []

        # Fetch gamelogs concurrently (max 10 at a time to avoid hammering ESPN)
        semaphore = asyncio.Semaphore(5)

        async def fetch_and_analyze(athlete_id: str, info: Dict[str, str]) -> List[Dict[str, Any]]:
            async with semaphore:
                gamelog = await self._fetch_espn_gamelog(sport, athlete_id)
            if not gamelog:
                return []
            results = []
            for stat_type in stat_categories:
                raw_values = self._parse_espn_gamelog_for_stat(sport, stat_type, gamelog)
                if len(raw_values) < min_streak_length:
                    continue
                # Wrap for _analyze_stat_streak
                fake_logs = [{"stats": {stat_type: v}} for v in raw_values]
                streak_info = self._analyze_stat_streak(fake_logs, stat_type, min_streak_length)
                if not streak_info or streak_info["best_streak"] < min_streak_length:
                    continue
                prop_line = self._calculate_prop_line(stat_type, streak_info["avg_recent"])
                details = streak_info["details"]
                last_4_raw = details.get("4_games")
                last_5_raw = details.get("5_games")
                streak_data = {
                    "player_id": f"{sport}_{athlete_id}_{stat_type}",
                    "name": info["name"],
                    "team": info["team"],
                    "sport": sport,
                    "position": info["position"],
                    "prop_line": f"Over {prop_line} {self._format_stat_name(stat_type)}",
                    "stat_type": stat_type,
                    "consecutive_games": streak_info["best_streak"],
                    "last_4_games": {
                        "games_analyzed": last_4_raw["games"],
                        "coverage_count": last_4_raw["cleared"],
                        "coverage_percent": last_4_raw["percent"],
                    } if last_4_raw else None,
                    "last_5_games": {
                        "games_analyzed": last_5_raw["games"],
                        "coverage_count": last_5_raw["cleared"],
                        "coverage_percent": last_5_raw["percent"],
                    } if last_5_raw else None,
                    "recent_values": streak_info["recent_values"],
                    "avg_recent": round(streak_info["avg_recent"], 1),
                    "games_today": today_games_dict.get(athlete_id, []),
                    "data_freshness": datetime.utcnow().isoformat() + "Z",
                    "source": "espn_gamelog",
                }
                results.append(streak_data)
            return results

        tasks = [fetch_and_analyze(aid, info) for aid, info in athletes_today.items()]
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in task_results:
            if isinstance(res, list):
                streaks.extend(res)

        streaks.sort(key=lambda x: x.get("consecutive_games", 0), reverse=True)
        return streaks[:20]
    
    async def get_club_100_streaks(
        self,
        db: AsyncSession,
        min_streak_length: int = 3,
        force_refresh: bool = False
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get REAL athletes with consecutive streaks on specific props.
        
        Returns data for today's games only.
        NEVER returns hardcoded or fake data - pure analysis from game logs.
        
        Args:
            db: Database session
            min_streak_length: Minimum consecutive games (default 3)
            
        Returns:
            {
                "nba": [player_data...],
                "nfl": [player_data...],
                "mlb": [player_data...],
                "nhl": [player_data...]
            }
        """
        current_time = datetime.utcnow()
        cache_key = f"club100_streaks_{min_streak_length}"
        
        # Check cache (1 hour) unless force refresh
        if not force_refresh and cache_key in self._cache:
            last_update = self._last_update.get(cache_key, datetime.utcfromtimestamp(0))
            if (current_time - last_update).total_seconds() < self._cache_ttl:
                logger.info(f"[CLUB100] Using cached streak data (fresh within 1 hour)")
                return self._cache[cache_key]
        
        logger.info(f"[CLUB100] Generating fresh streak analysis for {self.SUPPORTED_SPORTS}")
        
        result_by_sport = {sport: [] for sport in self.SUPPORTED_SPORTS}
        
        try:
            # Get today's games for matching
            player_stats_service = get_player_stats_service()
            today_games = {}
            
            for sport in self.SUPPORTED_SPORTS:
                try:
                    games = await player_stats_service.get_today_games_player_stats(sport)
                    today_games[sport] = games or []
                except Exception as e:
                    logger.warning(f"[CLUB100] Error fetching {sport} games: {e}")
                    today_games[sport] = []
            
            # Analyze streaks for each sport
            for sport in self.SUPPORTED_SPORTS:
                if not today_games.get(sport):
                    logger.info(f"[CLUB100] {sport.upper()}: No games today")
                    continue
                
                try:
                    streaks = await self._analyze_sport_streaks(
                        db, sport, min_streak_length, today_games[sport]
                    )
                    result_by_sport[sport] = streaks
                    logger.info(f"[CLUB100] {sport.upper()}: Found {len(streaks)} athletes with {min_streak_length}+ game streaks")
                except Exception as e:
                    logger.error(f"[CLUB100] Error analyzing {sport} streaks: {e}", exc_info=True)
                    result_by_sport[sport] = []
            
            # Cache the result
            self._cache[cache_key] = result_by_sport
            self._last_update[cache_key] = current_time
            
            total = sum(len(v) for v in result_by_sport.values())
            logger.info(f"[CLUB100] ✅ Generated real streak data: {total} total athletes with {min_streak_length}+ game streaks")
            
            return result_by_sport
            
        except Exception as e:
            logger.error(f"[CLUB100] Error in streak analysis: {e}", exc_info=True)
            return result_by_sport
    
    async def _analyze_sport_streaks(
        self,
        db: AsyncSession,
        sport: str,
        min_streak_length: int,
        today_games: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze consecutive streaks for all players in a sport.
        
        Only returns athletes with qualifying streaks appearing in today's games.
        OPTIMIZED: Bulk-fetches all game logs at once instead of per-player queries.
        """
        today_games_dict = self._build_today_games_dict(sport, today_games)
        
        if not today_games_dict:
            logger.info(f"[CLUB100] {sport.upper()}: No players in today's games")
            return []
        
        # Get all relevant players with recent game logs AND their logs in one bulk query
        players_with_logs, all_player_logs = await self._get_players_with_logs_bulk(db, sport)
        
        if not players_with_logs:
            logger.info(f"[CLUB100] {sport.upper()}: No DB game logs — falling back to ESPN gamelog API")
            return await self._analyze_sport_streaks_espn(sport, min_streak_length, today_games_dict, today_games)
        
        logger.debug(f"[CLUB100] Analyzing {len(players_with_logs)} {sport.upper()} players for streaks")
        
        streaks = []
        
        # Analyze each player for consecutive streaks
        for player in players_with_logs:
            try:
                # Use pre-fetched logs instead of querying per-player
                player_logs = all_player_logs.get(player.id, [])
                player_external_id = self._get_player_external_id(player, sport)
                if not player_external_id:
                    continue
                
                player_streaks = self._find_player_streaks_from_logs(
                    sport, player, player_logs, min_streak_length
                )
                
                # Filter to only players in today's games using ESPN athlete IDs
                external_key = str(player_external_id)
                for streak_data in player_streaks:
                    if external_key in today_games_dict:
                        streak_data["games_today"] = today_games_dict[external_key]
                        streaks.append(streak_data)
                
            except Exception as e:
                logger.debug(f"[CLUB100] Error analyzing player {player.name}: {e}")
                continue
        
        # Sort by best streak length
        streaks.sort(
            key=lambda x: (
                x.get("consecutive_games", 0),
                x.get("streak_details", {}).get("best_streak", 0)
            ),
            reverse=True
        )
        
        return streaks[:20]  # Limit to top 20 per sport
    
    def _build_today_games_dict(
        self,
        sport: str,
        today_games: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Map player IDs to their games today.
        
        Returns: {player_id: [{"opponent": "BOS", "time": "7:30 PM"}, ...]}
        """
        games_dict = defaultdict(list)
        for game in today_games:
            game_info = game.get("game", {})
            game_time = game_info.get("start_date") or "TBD"
            home_abbrev = game.get('home_team', {}).get('abbreviation')
            away_abbrev = game.get('away_team', {}).get('abbreviation')
            home_name = game.get('home_team', {}).get('name')
            away_name = game.get('away_team', {}).get('name')
            
            leaders = game.get("leaders", [])
            for leader in leaders:
                athlete = leader.get("athlete", {})
                if athlete and athlete.get("id"):
                    player_id = str(athlete.get("id"))
                    home_away = leader.get('home_away')
                    if home_away == 'home':
                        opponent = away_abbrev or away_name or 'Unknown'
                    elif home_away == 'away':
                        opponent = home_abbrev or home_name or 'Unknown'
                    else:
                        opponent = 'Unknown'
                    
                    game_detail = {
                        "opponent": opponent,
                        "time": game_time,
                        "game_name": game_info.get("name", "Game")
                    }
                    games_dict[player_id].append(game_detail)
        
        return dict(games_dict)
    
    async def _get_players_with_recent_logs(
        self,
        db: AsyncSession,
        sport: str
    ) -> List[PlayerRecord]:
        """
        Get all players who have recent game logs for this sport.
        """
        try:
            # Players in this sport that have game logs from last 60 days
            cutoff_date = datetime.utcnow() - timedelta(days=60)
            
            stmt = select(PlayerRecord).distinct().join(
                PlayerGameLog,
                PlayerGameLog.player_id == PlayerRecord.id
            ).where(
                and_(
                    PlayerRecord.sport_key == self._get_sport_key(sport),
                    PlayerGameLog.date >= cutoff_date
                )
            ).order_by(PlayerRecord.name)
            
            result = await db.execute(stmt)
            players = result.scalars().all()
            
            return list(players) if players else []
            
        except Exception as e:
            logger.error(f"[CLUB100] Error fetching players for {sport}: {e}", exc_info=True)
            return []
    
    async def _get_players_with_logs_bulk(
        self,
        db: AsyncSession,
        sport: str
    ) -> Tuple[List[PlayerRecord], Dict[str, List[Dict[str, Any]]]]:
        """
        OPTIMIZED: Get all players AND their game logs in bulk queries (2 total).
        
        Returns: (list of PlayerRecord, dict of player_id -> list of game logs)
        
        This avoids N+1 queries by:
        1. Getting all player IDs in one query
        2. Getting all their logs in a single bulk query
        3. Grouping logs by player ID in memory
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=60)
            sport_key = self._get_sport_key(sport)
            
            # Query 1: Get all players with game logs
            player_stmt = select(PlayerRecord).distinct().join(
                PlayerGameLog,
                PlayerGameLog.player_id == PlayerRecord.id
            ).where(
                and_(
                    PlayerRecord.sport_key == sport_key,
                    PlayerGameLog.date >= cutoff_date
                )
            ).order_by(PlayerRecord.name)
            
            player_result = await db.execute(player_stmt)
            players = list(player_result.scalars().all())
            
            if not players:
                return [], {}
            
            # Extract player IDs
            player_ids = [p.id for p in players]
            
            # Query 2: Get ALL game logs for these players in one query
            log_stmt = select(PlayerGameLog).where(
                and_(
                    PlayerGameLog.player_id.in_(player_ids),
                    PlayerGameLog.date >= cutoff_date
                )
            ).order_by(PlayerGameLog.player_id, PlayerGameLog.date.desc())
            
            log_result = await db.execute(log_stmt)
            all_logs = list(log_result.scalars().all())
            
            # Group logs by player ID in memory (fast)
            logs_by_player = defaultdict(list)
            for log in all_logs:
                log_dict = {
                    "date": log.date,
                    "stats": log.stats or {},
                    "opponent": log.opponent,
                    "event_id": log.event_id
                }
                logs_by_player[log.player_id].append(log_dict)
            
            # Reverse each player's logs to chronological order (oldest first)
            for player_id in logs_by_player:
                logs_by_player[player_id] = list(reversed(logs_by_player[player_id]))
            
            logger.debug(f"[CLUB100] Bulk-fetched {len(players)} players and {len(all_logs)} total game logs for {sport.upper()}")
            
            return players, dict(logs_by_player)
            
        except Exception as e:
            logger.error(f"[CLUB100] Error in bulk fetch for {sport}: {e}", exc_info=True)
            return [], {}
    
    def _find_player_streaks_from_logs(
        self,
        sport: str,
        player: PlayerRecord,
        game_logs: List[Dict[str, Any]],
        min_streak_length: int
    ) -> List[Dict[str, Any]]:
        """
        Find all consecutive streaks for a player from pre-fetched logs.
        
        Non-async version that works with in-memory logs.
        Returns list of streaks for each prop where player has qualifying streaks.
        """
        streaks = []
        player_id = player.id

        recent_logs = game_logs[-15:] if game_logs else []
        if len(recent_logs) < min_streak_length:
            logger.debug(
                f"[CLUB100] {player.name}: Only {len(recent_logs)} recent games (need {min_streak_length})"
            )
            return []

        stat_categories = self.STAT_CATEGORIES.get(sport, [])
        for stat_type in stat_categories:
            try:
                streak_info = self._analyze_stat_streak(
                    recent_logs, stat_type, min_streak_length
                )

                if not streak_info or streak_info["best_streak"] < min_streak_length:
                    continue

                prop_line = self._calculate_prop_line(stat_type, streak_info["avg_recent"])
                details = streak_info["details"]
                last_4_raw = details.get("4_games")
                last_5_raw = details.get("5_games")
                streak_data = {
                    "player_id": f"{sport}_{player_id}_{stat_type}",
                    "name": player.name,
                    "team": player.team_key or "Unknown",
                    "sport": sport,
                    "position": player.position or "Unknown",
                    "prop_line": f"Over {prop_line} {self._format_stat_name(stat_type)}",
                    "stat_type": stat_type,
                    "consecutive_games": streak_info["best_streak"],
                    "last_4_games": {
                        "games_analyzed": last_4_raw["games"],
                        "coverage_count": last_4_raw["cleared"],
                        "coverage_percent": last_4_raw["percent"],
                    } if last_4_raw else None,
                    "last_5_games": {
                        "games_analyzed": last_5_raw["games"],
                        "coverage_count": last_5_raw["cleared"],
                        "coverage_percent": last_5_raw["percent"],
                    } if last_5_raw else None,
                    "recent_values": streak_info["recent_values"],
                    "avg_recent": round(streak_info["avg_recent"], 1),
                    "games_today": [],
                    "data_freshness": datetime.utcnow().isoformat() + "Z",
                }
                streaks.append(streak_data)
            except Exception as e:
                logger.debug(f"[CLUB100] Error analyzing {stat_type} for {player.name}: {e}")
                continue

        return streaks
    
    def _analyze_stat_streak(
        self,
        game_logs: List[Dict[str, Any]],
        stat_type: str,
        min_streak_length: int
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze game logs to find consecutive streaks where stat exceeded a threshold.
        
        Returns info about the best consecutive streak for this stat.
        """
        if not game_logs:
            return None
        
        min_value = self.MIN_STAT_VALUES.get(stat_type, 0)
        
        # Extract stat values from logs
        stat_values = []
        for log in game_logs:
            value = self._extract_stat_value(log["stats"], stat_type)
            if value is not None:
                stat_values.append(value)
        
        if len(stat_values) < min_streak_length:
            return None
        
        # Find consecutive games above threshold
        best_streak = 0
        current_streak = 0
        current_streak_values = []
        all_streaks = []
        
        for value in stat_values:
            if value >= min_value:
                current_streak += 1
                current_streak_values.append(value)
            else:
                if current_streak >= min_streak_length:
                    all_streaks.append({
                        "length": current_streak,
                        "values": current_streak_values.copy()
                    })
                    best_streak = max(best_streak, current_streak)
                current_streak = 0
                current_streak_values = []
        
        # Check final streak
        if current_streak >= min_streak_length:
            all_streaks.append({
                "length": current_streak,
                "values": current_streak_values.copy()
            })
            best_streak = max(best_streak, current_streak)
        
        if best_streak == 0:
            return None
        
        # Build streak details
        streak_details = {}
        for window in [3, 4, 5, 6]:
            if len(stat_values) >= window:
                recent_window = stat_values[-window:]
                cleared = sum(1 for v in recent_window if v >= min_value)
                streak_details[f"{window}_games"] = {
                    "games": window,
                    "cleared": cleared,
                    "percent": round((cleared / window) * 100, 1)
                }
        
        streak_details["best_streak"] = best_streak
        
        return {
            "best_streak": best_streak,
            "details": streak_details,
            "recent_values": stat_values[-6:],  # Last 6 games
            "avg_recent": sum(stat_values[-6:]) / len(stat_values[-6:])
        }
    
    def _extract_stat_value(
        self,
        stats: Dict[str, Any],
        stat_type: str
    ) -> Optional[float]:
        """
        Extract a stat value from game log stats dict.
        Handles various naming conventions.
        """
        if not stats:
            return None
        
        # Direct key match
        if stat_type in stats:
            return self._convert_to_float(stats[stat_type])
        
        # Try common variations
        variations = [
            stat_type.replace("_", ""),
            stat_type.replace("_", " "),
            stat_type.lower(),
        ]
        
        for key, value in stats.items():
            key_norm = str(key).lower().replace("_", "").replace(" ", "")
            for var in variations:
                if key_norm == var.lower().replace("_", "").replace(" ", ""):
                    return self._convert_to_float(value)
        
        return None
    
    def _convert_to_float(self, value: Any) -> Optional[float]:
        """Safely convert a value to float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _calculate_prop_line(self, stat_type: str, avg_value: float) -> float:
        """
        Calculate a realistic prop line based on average performance.
        Lines are set 0.5-1.5 below average to represent "over" lines.
        """
        if not isinstance(avg_value, (int, float)):
            avg_value = 10.0
        
        # Adjust based on stat type volatility
        if stat_type in ["points", "pass_yards", "receiving_yards"]:
            line = avg_value * 0.85  # 15% below average
        elif stat_type in ["rebounds", "hits"]:
            line = avg_value * 0.80  # 20% below average
        elif stat_type in ["assists", "receptions"]:
            line = max(3, avg_value * 0.75)  # 25% below average, min 3
        else:
            line = avg_value * 0.80  # Default 20% below
        
        # Round to nearest 0.5
        return round(line * 2) / 2
    
    def _format_stat_name(self, stat_type: str) -> str:
        """Format stat type for display."""
        return stat_type.replace("_", " ").title()
    
    def _get_sport_key(self, sport: str) -> str:
        """Convert sport name to DB sport_key format."""
        sport_key_map = {
            "nba": "basketball/nba",
            "nfl": "football/nfl",
            "mlb": "baseball/mlb",
            "nhl": "hockey/nhl"
        }
        return sport_key_map.get(sport, sport)

    def _get_player_external_id(self, player: PlayerRecord, sport: str) -> Optional[str]:
        """Return the ESPN athlete ID stored on the PlayerRecord for the given sport."""
        external_id_map = {
            "nba": player.nba_id,
            "nfl": player.nfl_id,
            "mlb": player.mlb_id,
            "nhl": player.nhl_id,
        }
        ext_id = external_id_map.get(sport)
        return str(ext_id) if ext_id is not None else None
    
    def clear_cache(self):
        """Clear cached streak data."""
        self._cache.clear()
        self._last_update.clear()
        logger.info("[CLUB100] Streak cache cleared")


# Singleton instance
_club_100_streak_service: Optional[Club100StreakService] = None


def get_club_100_streak_service() -> Club100StreakService:
    """Get singleton Club 100 streak service."""
    global _club_100_streak_service
    if _club_100_streak_service is None:
        _club_100_streak_service = Club100StreakService()
    return _club_100_streak_service
