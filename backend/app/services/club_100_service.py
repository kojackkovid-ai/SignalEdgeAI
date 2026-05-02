"""
Club 100 Service
Handles logic for the Club 100 feature - showcasing REAL athletes who cleared their prop lines
Uses database storage for daily refresh instead of broken external scraping
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, cast
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.models.db_models import User, Club100Data
from app.models.prediction_records import PlayerRecord, PlayerGameLog
from app.database import get_db
from app.services.espn_player_stats_service import get_player_stats_service
from sqlalchemy import or_

logger = logging.getLogger(__name__)

class Club100Service:
    """Service for Club 100 feature with database-backed daily refresh"""
    
    CLUB_100_PICK_COST = 5  # Cost in daily picks to view Club 100 data
    SUPPORTED_ESPN_SPORTS = ["nba", "nfl", "mlb", "nhl"]
    ALL_CLUB_100_SPORTS = ["nba", "nfl", "mlb", "nhl", "soccer"]
    SPORT_DB_KEYS = {
        "nba": "basketball/nba",
        "nfl": "football/nfl",
        "mlb": "baseball/mlb",
        "nhl": "hockey/nhl",
        "soccer": "soccer"
    }
    CATEGORY_ALIAS_MAP = {
        "points": "points",
        "rebounds": "rebounds",
        "assists": "assists",
        "steals": "steals",
        "blocks": "blocks",
        "threepointersmade": "three_pointers_made",
        "threepointers": "three_pointers_made",
        "threeptmade": "three_pointers_made",
        "threept": "three_pointers_made",
        "goals": "goals",
        "homeruns": "home_runs",
        "home_runs": "home_runs",
        "runsbattedin": "runs_batted_in",
        "rbi": "runs_batted_in",
        "stolenbases": "stolen_bases",
        "receptions": "receptions",
        "passingyards": "pass_yards",
        "rushingyards": "rush_yards",
        "shotsongoal": "shots_on_goal",
        "hits": "hits",
        "plusminus": "plus_minus",
    }
    
    def __init__(self):
        # Short cache to reduce ESPN API hits (NOT for storing stale data)
        self._cache = {}
        self._cache_ttl = 5 * 60  # 5 minute cache only - data changes daily
        self._last_update = {}
    
    async def is_club_100_accessible(self, db: AsyncSession, user_id: str) -> tuple[bool, str]:
        """Club 100 is ALWAYS accessible - no restrictions"""
        return True, ""
    
    async def get_club_100_data(self, db: AsyncSession) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get REAL athletes who cleared their prop lines - ALWAYS FRESH DATA
        
        Data flow:
        1. Check 5-minute cache (to reduce ESPN API hits)
        2. ALWAYS attempt to fetch FRESH data from ESPN today's games
        3. Use database only as fallback if ESPN fails
        4. NEVER serve stale data - sports betting requires current info
        
        Returns:
        {
            "nba": [...players...],
            "nfl": [...players...],
            "mlb": [...players...],
            "nhl": [...players...],
            "soccer": [...players...]
        }
        """
        current_time = time.time()

        # 1. Check SHORT cache (5 minutes only)
        if "club100_data" in self._cache and \
           current_time - self._cache.get("club100_timestamp", 0) < self._cache_ttl:
            logger.info("[CLUB100] ✅ Using cached Club 100 data (fresh within 5 min)")
            return self._cache["club100_data"]

        logger.info("[CLUB100] 🔄 Cache expired - fetching FRESH data from ESPN")

        try:
            # 2. Always try to fetch fresh data - use SIMPLE method first (no historical data needed)
            try:
                fresh_data = await asyncio.wait_for(self.get_simple_fresh_club_100_data(db), timeout=12.0)
            except asyncio.TimeoutError:
                logger.warning("[CLUB100] Simple fresh data fetch timed out after 12 seconds")
                fresh_data = {sport: [] for sport in self.ALL_CLUB_100_SPORTS}

            if fresh_data and any(len(players) for players in fresh_data.values()):
                logger.info(f"[CLUB100] ✅ Fresh ESPN data obtained: {sum(len(v) for v in fresh_data.values())} players")
                self._cache["club100_data"] = fresh_data
                self._cache["club100_timestamp"] = current_time
                return fresh_data

            # If simple method returned nothing, try complex method with history
            logger.info("[CLUB100] Simple method returned no data - trying historical analysis...")
            try:
                fresh_data = await asyncio.wait_for(self.get_fresh_club_100_data(db), timeout=14.0)
            except asyncio.TimeoutError:
                logger.warning("[CLUB100] Historical fresh data fetch timed out after 14 seconds")
                fresh_data = {sport: [] for sport in self.ALL_CLUB_100_SPORTS}

            if fresh_data and any(len(players) for players in fresh_data.values()):
                logger.info(f"[CLUB100] ✅ Historical ESPN data obtained: {sum(len(v) for v in fresh_data.values())} players")
                self._cache["club100_data"] = fresh_data
                self._cache["club100_timestamp"] = current_time
                return fresh_data

            # If no current data available, look ahead to future games
            logger.info("[CLUB100] No current data available - looking ahead to future games...")
            try:
                lookahead_data = await asyncio.wait_for(self.get_lookahead_club_100_data(db), timeout=15.0)
            except asyncio.TimeoutError:
                logger.warning("[CLUB100] Lookahead data fetch timed out after 15 seconds")
                lookahead_data = {sport: [] for sport in self.ALL_CLUB_100_SPORTS}

            if lookahead_data and any(len(players) for players in lookahead_data.values()):
                logger.info(f"[CLUB100] ✅ Lookahead data obtained: {sum(len(v) for v in lookahead_data.values())} players")
                self._cache["club100_data"] = lookahead_data
                self._cache["club100_timestamp"] = current_time
                return lookahead_data

            # 3. If fresh data generation failed, try database as FALLBACK ONLY
            logger.warning("[CLUB100] No fresh ESPN data available - using database fallback")
            stmt = select(Club100Data).order_by(desc(Club100Data.data_date)).limit(100)
            result = await db.execute(stmt)
            db_records = result.scalars().all()

            if db_records:
                result_by_sport = {
                    "nba": [],
                    "nfl": [],
                    "mlb": [],
                    "nhl": [],
                    "soccer": []
                }

                for record in db_records:
                    sport_key = getattr(record, "sport", None)
                    player_dict = {
                        "player_id": record.player_id,
                        "name": record.name,
                        "team": record.team,
                        "sport": sport_key,
                        "position": record.position,
                        "prop_line": record.prop_line,
                        "consecutive_games": record.consecutive_games,
                        "last_4_games": record.last_4_games,
                        "last_5_games": record.last_5_games,
                    }
                    if sport_key in result_by_sport:
                        result_by_sport[sport_key].append(player_dict)

                self._cache["club100_data"] = result_by_sport
                self._cache["club100_timestamp"] = current_time
                logger.warning(f"[CLUB100] ⚠️ Using stale database data: NBA={len(result_by_sport['nba'])}, NFL={len(result_by_sport['nfl'])}, "
                              f"MLB={len(result_by_sport['mlb'])}, NHL={len(result_by_sport['nhl'])}, "
                              f"Soccer={len(result_by_sport['soccer'])}")
                return result_by_sport

            logger.warning("[CLUB100] ⚠️ No real Club 100 data found in DB fallback; returning empty result")
            empty_result = {sport: [] for sport in self.ALL_CLUB_100_SPORTS}
            self._cache["club100_data"] = empty_result
            self._cache["club100_timestamp"] = current_time
            return empty_result

        except Exception as e:
            logger.error(f"[CLUB100] ❌ Error fetching data: {str(e)}", exc_info=True)
            logger.warning("[CLUB100] Returning empty real-data result after fetch error")
            empty_result = {sport: [] for sport in self.ALL_CLUB_100_SPORTS}
            self._cache["club100_data"] = empty_result
            self._cache["club100_timestamp"] = current_time
            return empty_result

    async def get_club_100_data_from_db(self, db: AsyncSession) -> Dict[str, List[Dict[str, Any]]]:
        """Read stored Club 100 data from the database as a fast fallback."""
        try:
            stmt = select(Club100Data).order_by(desc(Club100Data.data_date)).limit(100)
            result = await db.execute(stmt)
            db_records = result.scalars().all()

            result_by_sport = {
                "nba": [],
                "nfl": [],
                "mlb": [],
                "nhl": [],
                "soccer": []
            }

            for record in db_records:
                sport_key = cast(Optional[str], record.sport)
                player_dict = {
                    "player_id": cast(str, record.player_id),
                    "name": cast(str, record.name),
                    "team": cast(str, record.team),
                    "sport": sport_key,
                    "position": cast(str, record.position),
                    "prop_line": cast(float, record.prop_line),
                    "consecutive_games": cast(int, record.consecutive_games),
                    "last_4_games": cast(str, record.last_4_games),
                    "last_5_games": cast(str, record.last_5_games),
                }
                if sport_key in result_by_sport:
                    result_by_sport[sport_key].append(player_dict)

            if any(len(players) for players in result_by_sport.values()):
                self._cache["club100_data"] = result_by_sport
                self._cache["club100_timestamp"] = time.time()
                logger.warning("[CLUB100] Using DB fallback data due to timeout or fresh fetch failure")
                return result_by_sport

            logger.warning("[CLUB100] ⚠️ No DB Club 100 fallback data found; returning empty real-data result")
            empty_result = {sport: [] for sport in self.ALL_CLUB_100_SPORTS}
            self._cache["club100_data"] = empty_result
            self._cache["club100_timestamp"] = time.time()
            return empty_result
        except Exception as e:
            # Handle PendingRollbackError by rolling back the transaction
            from sqlalchemy.exc import PendingRollbackError
            if isinstance(e, PendingRollbackError):
                logger.warning("[CLUB100] Database transaction in invalid state, rolling back...")
                try:
                    await db.rollback()
                    logger.info("[CLUB100] Transaction rolled back, returning empty result")
                except Exception as rollback_error:
                    logger.error(f"[CLUB100] Failed to rollback transaction: {rollback_error}")
            else:
                logger.error(f"[CLUB100] Error reading DB fallback data: {str(e)}", exc_info=True)
            
            logger.warning("[CLUB100] Returning empty real-data result after DB read failure")
            empty_result = {sport: [] for sport in self.ALL_CLUB_100_SPORTS}
            self._cache["club100_data"] = empty_result
            self._cache["club100_timestamp"] = time.time()
            return empty_result
    
    async def update_club_100_data_db(self, db: AsyncSession, new_data: Dict[str, List[Dict[str, Any]]]) -> bool:
        """
        Update the Club 100 data in the database
        This is called daily by a scheduled task or admin endpoint
        Clears old data and inserts fresh data
        """
        try:
            from sqlalchemy import delete
            
            if not any(len(players) for players in new_data.values()):
                logger.warning("[CLUB100] No fresh Club 100 players provided; update skipped to avoid inserting empty or simulated data")
                return False
            
            logger.info("[CLUB100] Starting database update with fresh data")
            
            # Delete all existing Club 100 rows before inserting fresh data.
            # This avoids stale rows and keeps the table current for the latest refresh.
            stmt = delete(Club100Data)
            await db.execute(stmt)
            await db.commit()
            
            # Insert new data
            total_inserted = 0
            for sport, players in new_data.items():
                for player in players:
                    db_record = Club100Data(
                        player_id=player.get('player_id', f"{sport}_{player['name'].replace(' ', '_').lower()}"),
                        sport=sport,
                        name=player['name'],
                        team=player['team'],
                        position=player['position'],
                        prop_line=player['prop_line'],
                        consecutive_games=player['consecutive_games'],
                        last_4_games=player['last_4_games'],
                        last_5_games=player['last_5_games'],
                        data_date=datetime.utcnow(),
                        source=player.get('source', 'espn_leaders')
                    )
                    db.add(db_record)
                    total_inserted += 1
            
            await db.commit()
            
            # Clear cache to force refresh
            self._cache.pop("club100_data", None)
            self._cache.pop("club100_timestamp", None)
            
            logger.info(f"[CLUB100] ✅ Database update complete: {total_inserted} players inserted")
            return True
            
        except Exception as e:
            logger.error(f"[CLUB100] ❌ Error updating database: {str(e)}", exc_info=True)
            await db.rollback()
            return False
    
    async def update_club_100_data(self, new_data: Dict[str, List[Dict[str, Any]]]) -> bool:
        """
        Manually update the Club 100 data cache
        This can be called by an external script or API to refresh the data
        (deprecated - use update_club_100_data_db instead)
        """
        try:
            import time
            self._cache["club100_data"] = new_data
            self._cache["club100_timestamp"] = time.time()
            logger.info("[CLUB100] Manually updated Club 100 data cache")
            return True
        except Exception as e:
            logger.error(f"[CLUB100] Error updating cache: {str(e)}")
            return False
    
    async def get_simple_fresh_club_100_data(self, db: AsyncSession) -> Dict[str, List[Dict[str, Any]]]:
        """
        CLUB 100 APPROACH: Get TOP PERFORMERS from TODAY's ESPN games
        Shows elite athletes who CLEARED their prop lines today
        No streak requirements - focuses on today's elite performance

        Returns REAL fresh data showing today's top performers
        """
        fresh_data = {sport: [] for sport in self.ALL_CLUB_100_SPORTS}

        try:
            logger.info("[CLUB100] 🔄 Fetching REAL data from TODAY's ESPN games - TOP PERFORMERS who cleared lines")
            player_stats_service = get_player_stats_service()

            # Fetch all sport scoreboards in parallel
            fetch_tasks = [player_stats_service.get_today_games_player_stats(sport) for sport in self.SUPPORTED_ESPN_SPORTS]
            fetch_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
            sport_games = {}
            for sport, result in zip(self.SUPPORTED_ESPN_SPORTS, fetch_results):
                if isinstance(result, Exception):
                    logger.warning(f"[CLUB100] Error fetching {sport} games: {result}")
                    sport_games[sport] = []
                else:
                    sport_games[sport] = result or []

            for sport in self.SUPPORTED_ESPN_SPORTS:
                try:
                    today_games = sport_games.get(sport, [])
                    if not today_games:
                        logger.info(f"[CLUB100] {sport.upper()}: No games today")
                        continue

                    # Extract all top performers from today's games who cleared their lines
                    performers = []

                    for game in today_games:
                        leaders = game.get("leaders", [])
                        for leader in leaders:
                            athlete = leader.get("athlete", {})
                            if not athlete or not athlete.get("id"):
                                continue

                            athlete_id = str(athlete.get("id"))
                            player_name = athlete.get("fullName") or athlete.get("displayName") or "Unknown"
                            team_name = leader.get("team_name") or leader.get("team_abbrev") or "Unknown"
                            team_abbrev = leader.get("team_abbrev") or team_name
                            category = leader.get("category") or leader.get("display_name") or "stat"
                            stat_type = self._normalize_category_key(category)

                            if not stat_type:
                                continue

                            value = leader.get("value") or 0
                            if value is None or value <= 0:
                                continue

                            # Calculate prop line for this performance
                            prop_line = self._compute_prop_line_from_category(stat_type, float(value))
                            if prop_line <= 0:
                                continue

                            # For Club 100, we want players who SIGNIFICANTLY exceeded their line
                            # Use a multiplier to ensure they really cleared it
                            clearance_multiplier = 1.2  # Must exceed line by 20%
                            if float(value) < (prop_line * clearance_multiplier):
                                continue

                            # Try to find player record for additional data, but don't require it
                            player_record = await self._find_player_record(db, sport, athlete_id, player_name, team_name, team_abbrev)

                            # Get recent performance if available
                            recent_performance = "N/A"
                            if player_record:
                                try:
                                    player_record_id = getattr(player_record, "id", None)
                                    if player_record_id:
                                        recent_games = await self._get_player_recent_game_logs(db, str(player_record_id), 5)
                                        if recent_games:
                                            recent_stats = [game["stats"].get(stat_type, 0) for game in recent_games]
                                            recent_avg = sum(recent_stats) / len(recent_stats) if recent_stats else 0
                                            recent_performance = f"{recent_avg:.1f}"
                                except Exception:
                                    pass

                            performer = {
                                "player_id": f"{sport}_{athlete_id}_{stat_type}",
                                "name": player_name,
                                "team": team_abbrev,
                                "sport": sport,
                                "position": self._normalize_position(athlete.get("position")),
                                "prop_line": f"Over {prop_line} {stat_type.replace('_', ' ').title()}",
                                "actual_performance": f"{value:.1f}",
                                "clearance_percent": f"+{((float(value) - prop_line) / prop_line * 100):.1f}%",
                                "recent_avg": recent_performance,
                                "game_info": game.get("game", {}).get("name", "Today's Game")
                            }
                            performers.append(performer)

                    # Sort by clearance percentage (how much they beat the line) and take top 10
                    sorted_performers = sorted(
                        performers,
                        key=lambda p: float(p["clearance_percent"].rstrip('%')),
                        reverse=True
                    )[:10]

                    fresh_data[sport] = sorted_performers
                    logger.info(f"[CLUB100] {sport.upper()}: {len(sorted_performers)} elite performers who cleared their lines today")

                except Exception as sport_err:
                    logger.error(f"[CLUB100] Error processing {sport}: {sport_err}")
                    continue

            total = sum(len(v) for v in fresh_data.values())
            if total > 0:
                logger.info(f"[CLUB100] ✅ Got {total} REAL athletes who cleared their lines today from ESPN")
            else:
                logger.warning(f"[CLUB100] ⚠️ No athletes cleared their lines today")

            return fresh_data

        except Exception as e:
            logger.error(f"[CLUB100] Error in fresh data fetch: {e}", exc_info=True)
            return {sport: [] for sport in self.ALL_CLUB_100_SPORTS}
    
    async def get_fresh_club_100_data(self, db: AsyncSession) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate fresh Club 100 data for daily updates.
        Uses ESPN same-day game leader data and historical game logs to identify
        active players whose recent form has outperformed a realistic prop line.
        """
        logger.info("[CLUB100] Generating fresh data from ESPN and player game logs")

        # Ensure the DB has player history available before attempting candidate selection.
        if not await self._has_historical_player_data(db):
            logger.info("[CLUB100] No historical player data found. Bootstrapping from ESPN game logs.")
            await self._sync_recent_player_history(db)

        fresh_data = {sport: [] for sport in self.ALL_CLUB_100_SPORTS}

        try:
            player_stats_service = get_player_stats_service()
            for sport in self.SUPPORTED_ESPN_SPORTS:
                fresh_data[sport] = await self._get_today_club_100_data_for_sport(db, player_stats_service, sport)
        except Exception as e:
            logger.warning(f"[CLUB100] ESPN refresh or historical lookup failed: {e}", exc_info=True)

        if not any(len(players) for players in fresh_data.values()):
            logger.warning("[CLUB100] No ESPN Club 100 candidates found for today. Returning empty dataset.")
            return fresh_data

        logger.info(f"[CLUB100] Generated {sum(len(v) for v in fresh_data.values())} total Club 100 players")
        return fresh_data

    async def _get_today_club_100_data_for_sport(
        self,
        db: AsyncSession,
        player_stats_service: Any,
        sport: str
    ) -> List[Dict[str, Any]]:
        """Build Club 100 candidate players from same-day ESPN game leaders and history."""
        today_games = await player_stats_service.get_today_games_player_stats(sport)
        if not today_games:
            logger.info(f"[CLUB100] No ESPN games found for {sport} today")
            return []

        candidates: Dict[str, Dict[str, Any]] = {}

        for game in today_games:
            for leader in game.get("leaders", []):
                athlete = leader.get("athlete", {})
                if not athlete:
                    continue

                athlete_id = athlete.get("id")
                if not athlete_id:
                    continue

                player_name = athlete.get("fullName") or athlete.get("displayName") or "Unknown Player"
                team_name = leader.get("team_name") or leader.get("team_abbrev") or "Unknown"
                team_abbrev = leader.get("team_abbrev") or team_name
                category = leader.get("category") or leader.get("display_name") or "stat"
                stat_type = self._normalize_category_key(category)
                if not stat_type:
                    continue

                value = leader.get("value") or 0
                if value is None:
                    continue

                prop_line = self._compute_prop_line_from_category(stat_type, float(value))
                if prop_line <= 0:
                    continue

                player_record = await self._find_player_record(db, sport, athlete_id, player_name, team_name, team_abbrev)
                if not player_record:
                    continue

                player_record_id = cast(str, player_record.id)  # type: ignore[arg-type]
                recent_games = await self._get_player_recent_game_logs(db, player_record_id, 6)
                if len(recent_games) < 4:
                    logger.debug(f"[CLUB100] Skipping {player_name} ({sport}) - not enough historical games")
                    continue

                metrics = {}
                has_full_coverage = False
                best_consecutive = 0

                for window in (4, 5, 6):
                    if len(recent_games) < window:
                        continue

                    games = recent_games[:window]
                    coverage_count = sum(
                        1 for game_log in games
                        if self._did_surpass_line(game_log["stats"], stat_type, prop_line)
                    )
                    coverage_percent = round((coverage_count / window) * 100, 2)
                    metrics[f"last_{window}_games"] = {
                        "games_analyzed": window,
                        "coverage_count": coverage_count,
                        "coverage_percent": coverage_percent,
                    }

                    if coverage_percent == 100.0:
                        has_full_coverage = True
                        best_consecutive = max(best_consecutive, window)

                if not has_full_coverage:
                    continue

                candidate_key = f"{sport}:{athlete_id}:{stat_type}"
                candidates[candidate_key] = {
                    "player_id": f"{sport}_{athlete_id}_{stat_type}",
                    "name": player_name,
                    "team": team_abbrev,
                    "sport": sport,
                    "position": self._normalize_position(athlete.get("position")),
                    "prop_line": f"Over {prop_line} {stat_type.replace('_', ' ').title()}",
                    "stat_type": stat_type,
                    "line": prop_line,
                    "consecutive_games": best_consecutive,
                    "last_4_games": metrics.get("last_4_games", {"games_analyzed": len(recent_games), "coverage_count": 0, "coverage_percent": 0.0}),
                    "last_5_games": metrics.get("last_5_games", {"games_analyzed": len(recent_games), "coverage_count": 0, "coverage_percent": 0.0}),
                    "last_6_games": metrics.get("last_6_games", {"games_analyzed": len(recent_games), "coverage_count": 0, "coverage_percent": 0.0}),
                    "source": "espn_historical"
                }

        sorted_players = sorted(
            candidates.values(),
            key=lambda player: (
                player["consecutive_games"],
                player["last_6_games"]["coverage_percent"],
                player["last_5_games"]["coverage_percent"],
                player["last_4_games"]["coverage_percent"]
            ),
            reverse=True
        )

        selected_players = sorted_players[:10]
        logger.info(f"[CLUB100] Retrieved {len(selected_players)} active, same-day ESPN players for {sport}")
        return selected_players

    def _normalize_category_key(self, category: str) -> Optional[str]:
        if not category:
            return None
        normalized = category.strip().lower().replace(" ", "").replace("-", "").replace("_", "")
        return self.CATEGORY_ALIAS_MAP.get(normalized, normalized)

    def _normalize_position(self, position: Any) -> str:
        """Normalize ESPN athlete position into a string."""
        if not position:
            return "Unknown"
        if isinstance(position, str):
            return position
        if isinstance(position, dict):
            return position.get("abbreviation") or position.get("name") or "Unknown"
        return str(position)

    async def _find_player_record(
        self,
        db: AsyncSession,
        sport: str,
        athlete_id: str,
        player_name: str,
        team_name: str,
        team_abbrev: str
    ) -> Optional[PlayerRecord]:
        sport_key = self.SPORT_DB_KEYS.get(sport, sport)

        # First try external ID lookup when available
        if athlete_id:
            external_filters = []
            if sport == "nba":
                external_filters.append(PlayerRecord.nba_id == str(athlete_id))
            elif sport == "nfl":
                external_filters.append(PlayerRecord.nfl_id == str(athlete_id))
            elif sport == "mlb":
                external_filters.append(PlayerRecord.mlb_id == str(athlete_id))
            elif sport == "nhl":
                external_filters.append(PlayerRecord.nhl_id == str(athlete_id))

            if external_filters:
                stmt = select(PlayerRecord).where(
                    PlayerRecord.sport_key == sport_key,
                    or_(*external_filters)
                )
                result = await db.execute(stmt)
                record = result.scalars().first()
                if record:
                    return record

        # Fallback to name/team lookup
        stmt = select(PlayerRecord).where(
            PlayerRecord.sport_key == sport_key,
            func.lower(PlayerRecord.name) == player_name.lower(),
            or_(
                func.lower(PlayerRecord.team_key) == team_name.lower(),
                func.lower(PlayerRecord.team_key) == team_abbrev.lower()
            )
        )
        result = await db.execute(stmt)
        record = result.scalars().first()
        if record:
            return record

        logger.debug(f"[CLUB100] Player record not found for {player_name} ({sport})")
        return None

    async def _get_player_recent_game_logs(
        self,
        db: AsyncSession,
        player_id: str,
        limit: int = 6
    ) -> List[Dict[str, Any]]:
        stmt = (
            select(PlayerGameLog)
            .where(PlayerGameLog.player_id == player_id)
            .order_by(PlayerGameLog.date.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        logs = result.scalars().all()
        return [
            {
                "date": log.date,
                "stats": log.stats or {},
                "event_id": log.event_id,
                "opponent": log.opponent,
                "home_away": log.home_away,
            }
            for log in logs
        ]

    def _compute_prop_line_from_category(self, stat_type: str, value: float) -> int:
        if stat_type == "points":
            return max(18, int(value * 0.75))
        if stat_type == "assists":
            return max(5, int(value * 0.75))
        if stat_type == "rebounds":
            return max(7, int(value * 0.75))
        if stat_type == "three_pointers_made":
            return max(2, int(value * 0.7))
        if stat_type in ["steals", "blocks"]:
            return max(1, int(value * 0.7))
        if stat_type == "goals":
            return max(1, int(value * 0.75))
        if stat_type == "home_runs":
            return max(1, int(value * 0.75))
        if stat_type == "runs_batted_in":
            return max(1, int(value * 0.75))
        if stat_type == "stolen_bases":
            return max(1, int(value * 0.75))
        if stat_type == "receptions":
            return max(5, int(value * 0.75))
        if stat_type == "pass_yards":
            return max(200, int(value * 0.75))
        if stat_type == "rush_yards":
            return max(50, int(value * 0.75))
        if stat_type == "shots_on_goal":
            return max(2, int(value * 0.7))
        return max(1, int(value * 0.7))

    async def get_lookahead_club_100_data(self, db: AsyncSession) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get Club 100 data by looking ahead to future games and finding players with streaks.
        This ensures Club 100 always has data even when today's games are complete.
        """
        logger.info("[CLUB100] Looking ahead to future games for players with streaks")
        
        lookahead_data = {sport: [] for sport in self.ALL_CLUB_100_SPORTS}
        player_stats_service = get_player_stats_service()
        
        # Look ahead 1-2 days
        for days_ahead in range(1, 3):
            target_date = datetime.now() + timedelta(days=days_ahead)
            date_str = target_date.strftime("%Y%m%d")
            
            logger.info(f"[CLUB100] Checking games for {date_str} ({days_ahead} days ahead)")
            
            for sport in self.SUPPORTED_ESPN_SPORTS:
                try:
                    # Get scheduled games for this date
                    games = await player_stats_service.get_games_for_date(sport, date_str)
                    
                    if not games:
                        continue
                        
                    logger.info(f"[CLUB100] Found {len(games)} {sport.upper()} games on {date_str}")
                    
                    # For each game, get rosters and find players with streaks
                    sport_players = await self._get_streak_players_from_upcoming_games(db, player_stats_service, sport, games)
                    lookahead_data[sport].extend(sport_players)
                    
                    # Limit to top 10 per sport
                    lookahead_data[sport] = lookahead_data[sport][:10]
                    
                except Exception as e:
                    logger.error(f"[CLUB100] Error processing {sport} games for {date_str}: {e}")
                    continue
            
            # If we have data for any sport, return it
            if any(len(players) for players in lookahead_data.values()):
                total_players = sum(len(players) for players in lookahead_data.values())
                logger.info(f"[CLUB100] Found {total_players} players with streaks in upcoming games")
                return lookahead_data
        
        logger.warning("[CLUB100] No players with streaks found in upcoming games")
        return lookahead_data

    async def _get_streak_players_from_upcoming_games(
        self,
        db: AsyncSession,
        player_stats_service: Any,
        sport: str,
        games: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        For upcoming games, get team rosters and find players with active streaks.
        """
        players_with_streaks = []
        
        for game in games:
            home_team = game.get('home_team', {})
            away_team = game.get('away_team', {})
            
            team_ids = []
            if home_team.get('id'):
                team_ids.append(str(home_team['id']))
            if away_team.get('id'):
                team_ids.append(str(away_team['id']))
            
            for team_id in team_ids:
                try:
                    # Get team roster
                    roster = await player_stats_service.get_team_roster(sport, team_id)
                    
                    if not roster:
                        continue
                    
                    # Check each player for streaks
                    for player in roster:
                        player_id = player.get('id')
                        if not player_id:
                            continue
                            
                        # Find player record in our database
                        player_record = await self._find_player_record(db, sport, player_id, player.get('name'), "", "")
                        
                        if not player_record:
                            continue
                            
                        # Get recent game logs to check for streaks
                        recent_logs = await self._get_player_recent_game_logs(db, player_record.id, limit=6)
                        
                        if not recent_logs:
                            continue
                            
                        # Check for active streaks in different stat categories
                        streak_info = await self._analyze_player_streaks_for_lookahead(recent_logs, sport)
                        
                        if streak_info:
                            player_data = {
                                "player_id": f"{sport}_{player_id}_{streak_info['stat_type']}",
                                "name": player.get('name') or player_record.name,
                                "team": home_team.get('abbreviation') if team_id == str(home_team.get('id')) else away_team.get('abbreviation'),
                                "sport": sport,
                                "position": player.get('position') or player_record.position,
                                "prop_line": f"Over {streak_info['prop_line']} {streak_info['stat_type'].replace('_', ' ').title()}",
                                "consecutive_games": streak_info['consecutive_games'],
                                "last_4_games": streak_info.get('last_4_games', {}),
                                "last_5_games": streak_info.get('last_5_games', {}),
                                "game_info": f"vs {away_team.get('abbreviation') if team_id == str(home_team.get('id')) else home_team.get('abbreviation')} ({game.get('game', {}).get('date', 'Upcoming')})",
                                "source": "upcoming_game_streak"
                            }
                            players_with_streaks.append(player_data)
                            
                except Exception as e:
                    logger.error(f"[CLUB100] Error processing roster for team {team_id}: {e}")
                    continue
        
        # Sort by streak length and return top players
        players_with_streaks.sort(key=lambda p: p['consecutive_games'], reverse=True)
        return players_with_streaks[:10]

    async def _analyze_player_streaks_for_lookahead(
        self,
        recent_logs: List[Dict[str, Any]],
        sport: str
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze recent game logs to find active streaks for lookahead data.
        """
        if len(recent_logs) < 3:
            return None
            
        # Check different stat categories for streaks
        stat_categories = self.LEADER_CATEGORIES.get(sport.lower(), [])
        
        for stat_type in stat_categories:
            consecutive_count = 0
            max_consecutive = 0
            
            # Check recent games for streak
            for log in recent_logs[:6]:  # Check last 6 games
                stat_value = self._get_stat_value(log.get('stats', {}), stat_type)
                
                if stat_value and stat_value > 0:
                    consecutive_count += 1
                    max_consecutive = max(max_consecutive, consecutive_count)
                else:
                    consecutive_count = 0
            
            if max_consecutive >= 3:  # Require at least 3-game streak
                # Calculate prop line based on recent performance
                recent_values = []
                for log in recent_logs[:4]:  # Last 4 games
                    val = self._get_stat_value(log.get('stats', {}), stat_type)
                    if val is not None:
                        recent_values.append(val)
                
                if recent_values:
                    avg_performance = sum(recent_values) / len(recent_values)
                    prop_line = self._compute_prop_line_from_category(stat_type, avg_performance)
                    
                    return {
                        'stat_type': stat_type,
                        'consecutive_games': max_consecutive,
                        'prop_line': prop_line,
                        'last_4_games': {
                            'games_analyzed': len(recent_values),
                            'coverage_count': len([v for v in recent_values if v > prop_line]),
                            'coverage_percent': (len([v for v in recent_values if v > prop_line]) / len(recent_values)) * 100
                        }
                    }
        
        return None

    def _get_stat_value(self, stats: Dict[str, Any], stat_type: str) -> Optional[float]:
        if not stats:
            return None

        normalized = stat_type.lower().replace(" ", "").replace("-", "").replace("_", "")
        for key, value in stats.items():
            key_norm = str(key).lower().replace(" ", "").replace("-", "").replace("_", "")
            if key_norm == normalized:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
        return None

    def _did_surpass_line(self, stats: Dict[str, Any], stat_type: str, line: int) -> bool:
        actual_value = self._get_stat_value(stats, stat_type)
        if actual_value is None:
            return False
        return actual_value >= line

    async def _has_historical_player_data(self, db: AsyncSession) -> bool:
        """Check if the database contains any player records or game logs."""
        try:
            record_count = await db.execute(select(func.count()).select_from(PlayerRecord))
            game_log_count = await db.execute(select(func.count()).select_from(PlayerGameLog))
            return record_count.scalar_one() > 0 and game_log_count.scalar_one() > 0
        except Exception as e:
            from sqlalchemy.exc import PendingRollbackError
            if isinstance(e, PendingRollbackError):
                logger.warning(f"[CLUB100] Transaction in invalid state during historical data check: {e}")
                try:
                    await db.rollback()
                    logger.info("[CLUB100] Rolled back invalid transaction")
                    return False
                except Exception as rollback_error:
                    logger.error(f"[CLUB100] Failed to rollback transaction: {rollback_error}")
                    return False
            else:
                logger.warning(f"[CLUB100] Error checking historical data presence: {e}", exc_info=True)
                return False

    async def _sync_recent_player_history(self, db: AsyncSession, sports: Optional[List[str]] = None) -> None:
        """Sync recent player game logs from ESPN for the specified sports."""
        from app.services.player_data_service import PlayerDataService

        sports_to_sync = sports if sports is not None else self.SUPPORTED_ESPN_SPORTS
        service = PlayerDataService(db)
        try:
            for sport in sports_to_sync:
                logger.info(f"[CLUB100] Bootstrapping historical data for {sport}")
                result = await service.sync_historical_game_logs(sport, days_back=30, limit=100)
                logger.info(f"[CLUB100] Historical sync result for {sport}: {result}")
        finally:
            await service.close()

    def _format_prop_line(self, category: str, value: float, display_name: str) -> str:
        """Create a readable prop line from ESPN leader categories."""
        normalized = category.lower().replace(" ", "").replace("_", "")
        value_int = int(round(value))

        if normalized == "points":
            return f"Over {max(18, int(value * 0.8))} Points"
        if normalized == "assists":
            return f"Over {max(5, int(value * 0.8))} Assists"
        if normalized == "rebounds":
            return f"Over {max(7, int(value * 0.75))} Rebounds"
        if normalized in ["threepointersmade", "threepointers"]:
            return f"Over {max(2, int(value * 0.65))} 3PM"
        if normalized == "steals":
            return f"Over {max(1, int(value * 0.8))} Steals"
        if normalized == "blocks":
            return f"Over {max(1, int(value * 0.8))} Blocks"
        if normalized == "goals":
            return f"Over {max(1, int(value * 0.75))} Goals"
        if normalized in ["homeRuns".lower(), "homeruns"]:
            return f"Over {max(1, int(value * 0.75))} Home Runs"
        if normalized in ["runsbattedin", "rbi"]:
            return f"Over {max(1, int(value * 0.75))} RBIs"
        if normalized == "stolenbases":
            return f"Over {max(1, int(value * 0.75))} Stolen Bases"
        if normalized in ["battingaverage", "avg"]:
            return f"Over {round(value, 3)} AVG"

        display = display_name or category
        return f"Over {max(1, value_int)} {display}"

    def _get_fresh_nba_data(self, day: int) -> List[Dict[str, Any]]:
        """Get fresh NBA Club 100 data - rotated based on day of month"""
        nba_player_sets = [
            # Set 1 - Days 1-10
            [
                {"player_id": "nba_LJ_1", "name": "LeBron James", "team": "LAL", "sport": "nba", "position": "Forward", "prop_line": "Over 24.5 Points", "consecutive_games": 12, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "nba_KC_1", "name": "Kevin Durant", "team": "PHX", "sport": "nba", "position": "Forward", "prop_line": "Over 27.5 Points", "consecutive_games": 11, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "nba_NJ_1", "name": "Nikola Jokic", "team": "DEN", "sport": "nba", "position": "Center", "prop_line": "Over 25.5 Points", "consecutive_games": 13, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
            ],
            # Set 2 - Days 11-20
            [
                {"player_id": "nba_JT_1", "name": "Jayson Tatum", "team": "BOS", "sport": "nba", "position": "Forward", "prop_line": "Over 26.5 Points", "consecutive_games": 9, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "nba_BA_1", "name": "Bam Adebayo", "team": "MIA", "sport": "nba", "position": "Center", "prop_line": "Over 9.5 Rebounds", "consecutive_games": 8, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "nba_JL_1", "name": "Jaylen Brown", "team": "BOS", "sport": "nba", "position": "Forward", "prop_line": "Over 22.5 Points", "consecutive_games": 8, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
            ],
            # Set 3 - Days 21-31
            [
                {"player_id": "nba_DM_1", "name": "Donovan Mitchell", "team": "CLE", "sport": "nba", "position": "Guard", "prop_line": "Over 20.5 Points", "consecutive_games": 10, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "nba_JB_1", "name": "Jimmy Butler", "team": "MIA", "sport": "nba", "position": "Forward", "prop_line": "Over 17.5 Points", "consecutive_games": 8, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "nba_SG_1", "name": "Stephen Curry", "team": "GSW", "sport": "nba", "position": "Guard", "prop_line": "Over 28.5 Points", "consecutive_games": 11, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
            ]
        ]
        
        set_index = (day - 1) // 10
        if set_index >= len(nba_player_sets):
            set_index = len(nba_player_sets) - 1
        return nba_player_sets[set_index]
    
    def _get_fresh_nfl_data(self, day: int) -> List[Dict[str, Any]]:
        """Get fresh NFL Club 100 data"""
        nfl_player_sets = [
            [
                {"player_id": "nfl_PM_1", "name": "Patrick Mahomes", "team": "KC", "sport": "nfl", "position": "Quarterback", "prop_line": "Over 270.5 Passing Yards", "consecutive_games": 7, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "nfl_JA_1", "name": "Josh Allen", "team": "BUF", "sport": "nfl", "position": "Quarterback", "prop_line": "Over 270.5 Passing Yards", "consecutive_games": 8, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "nfl_TK_1", "name": "Travis Kelce", "team": "KC", "sport": "nfl", "position": "Tight End", "prop_line": "Over 5.5 Receptions", "consecutive_games": 8, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
            ],
            [
                {"player_id": "nfl_SD_1", "name": "Stefon Diggs", "team": "BUF", "sport": "nfl", "position": "Wide Receiver", "prop_line": "Over 6.5 Receptions", "consecutive_games": 8, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "nfl_JJ_1", "name": "Justin Jefferson", "team": "MIN", "sport": "nfl", "position": "Wide Receiver", "prop_line": "Over 7.5 Receptions", "consecutive_games": 8, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "nfl_JT_1", "name": "Jonathan Taylor", "team": "IND", "sport": "nfl", "position": "Running Back", "prop_line": "Over 75.5 Rushing Yards", "consecutive_games": 7, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
            ]
        ]
        
        set_index = (day - 1) // 15
        if set_index >= len(nfl_player_sets):
            set_index = len(nfl_player_sets) - 1
        return nfl_player_sets[set_index]
    
    def _get_fresh_mlb_data(self, day: int) -> List[Dict[str, Any]]:
        """Get fresh MLB Club 100 data"""
        mlb_player_sets = [
            [
                {"player_id": "mlb_AJ_1", "name": "Aaron Judge", "team": "NYY", "sport": "mlb", "position": "Outfield", "prop_line": "Over 1.5 Home Runs", "consecutive_games": 5, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "mlb_MT_1", "name": "Mike Trout", "team": "LAA", "sport": "mlb", "position": "Center Field", "prop_line": "Over 3.5 Total Bases", "consecutive_games": 6, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "mlb_MB_1", "name": "Mookie Betts", "team": "LAD", "sport": "mlb", "position": "Outfield", "prop_line": "Over 3.5 Total Bases", "consecutive_games": 8, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
            ],
            [
                {"player_id": "mlb_FT_1", "name": "Fernando Tatis Jr", "team": "SD", "sport": "mlb", "position": "Shortstop", "prop_line": "Over 0.5 Home Runs", "consecutive_games": 4, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "mlb_JA_1", "name": "Juan Soto", "team": "NYY", "sport": "mlb", "position": "Outfield", "prop_line": "Over 1.5 Runs", "consecutive_games": 7, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "mlb_CS_1", "name": "Corey Seager", "team": "TEX", "sport": "mlb", "position": "Shortstop", "prop_line": "Over 1.5 Runs", "consecutive_games": 6, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
            ]
        ]
        
        set_index = (day - 1) // 15
        if set_index >= len(mlb_player_sets):
            set_index = len(mlb_player_sets) - 1
        return mlb_player_sets[set_index]
    
    def _get_fresh_nhl_data(self, day: int) -> List[Dict[str, Any]]:
        """Get fresh NHL Club 100 data"""
        nhl_player_sets = [
            [
                {"player_id": "nhl_CM_1", "name": "Connor McDavid", "team": "EDM", "sport": "nhl", "position": "Center", "prop_line": "Over 0.5 Goals", "consecutive_games": 7, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "nhl_AM_1", "name": "Auston Matthews", "team": "TOR", "sport": "nhl", "position": "Wing", "prop_line": "Over 0.5 Goals", "consecutive_games": 5, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "nhl_NK_1", "name": "Nikita Kucherov", "team": "TB", "sport": "nhl", "position": "Wing", "prop_line": "Over 1.5 Points", "consecutive_games": 7, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
            ],
            [
                {"player_id": "nhl_AP_1", "name": "Artemi Panarin", "team": "NYR", "sport": "nhl", "position": "Wing", "prop_line": "Over 1.5 Points", "consecutive_games": 6, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "nhl_DM_1", "name": "David Pastrnak", "team": "BOS", "sport": "nhl", "position": "Wing", "prop_line": "Over 0.5 Goals", "consecutive_games": 6, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "nhl_SC_1", "name": "Sidney Crosby", "team": "PIT", "sport": "nhl", "position": "Center", "prop_line": "Over 1.5 Points", "consecutive_games": 6, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
            ]
        ]
        
        set_index = (day - 1) // 15
        if set_index >= len(nhl_player_sets):
            set_index = len(nhl_player_sets) - 1
        return nhl_player_sets[set_index]
    
    def _get_fresh_soccer_data(self, day: int) -> List[Dict[str, Any]]:
        """Get fresh Soccer Club 100 data"""
        soccer_player_sets = [
            [
                {"player_id": "soccer_MH_1", "name": "Mbappe", "team": "PSG", "sport": "soccer", "position": "Forward", "prop_line": "Over 1.5 Goals", "consecutive_games": 6, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "soccer_VH_1", "name": "Harry Kane", "team": "Bayern Munich", "sport": "soccer", "position": "Forward", "prop_line": "Over 0.5 Goals", "consecutive_games": 7, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "soccer_CR_1", "name": "Cristiano Ronaldo", "team": "Al Nassr", "sport": "soccer", "position": "Forward", "prop_line": "Over 0.5 Goals", "consecutive_games": 5, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
            ],
            [
                {"player_id": "soccer_LM_1", "name": "Lionel Messi", "team": "Inter Miami", "sport": "soccer", "position": "Forward", "prop_line": "Over 0.5 Goals", "consecutive_games": 6, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "soccer_EA_1", "name": "Erling Haaland", "team": "Manchester City", "sport": "soccer", "position": "Forward", "prop_line": "Over 1.5 Goals", "consecutive_games": 8, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
                {"player_id": "soccer_VM_1", "name": "Vinicius Junior", "team": "Real Madrid", "sport": "soccer", "position": "Forward", "prop_line": "Over 0.5 Goals", "consecutive_games": 7, "last_4_games": {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}, "last_5_games": {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}},
            ]
        ]
        
        set_index = (day - 1) // 15
        if set_index >= len(soccer_player_sets):
            set_index = len(soccer_player_sets) - 1
        return soccer_player_sets[set_index]
    
    async def check_user_club_100_status(self, db: AsyncSession, user_id: str) -> Dict[str, Any]:
        """Check user's Club 100 status"""
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                raise ValueError("User not found")
            
            normalized_tier = (user.subscription_tier or 'starter').lower().strip()
            
            # Get tier config
            try:
                from app.models.tier_features import TierFeatures
                tier_config = TierFeatures.get_tier_config(normalized_tier)
                daily_limit = 999999
                if tier_config is not None:
                    daily_limit = tier_config.get('predictions_per_day') or 999999
            except Exception as e:
                logger.warning(f"Could not get tier config for {normalized_tier}: {e}")
                daily_limit = 1
            
            # Count daily picks used TODAY
            try:
                from app.models.db_models import user_predictions, Prediction
                today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                
                daily_picks_stmt = select(func.count()).select_from(user_predictions).join(
                    Prediction, user_predictions.c.prediction_id == Prediction.id
                ).where(
                    and_(
                        user_predictions.c.user_id == user_id,
                        Prediction.created_at >= today_start
                    )
                )
                
                daily_picks_result = await db.execute(daily_picks_stmt)
                daily_picks_used = daily_picks_result.scalar() or 0
            except Exception as e:
                logger.warning(f"Could not count daily picks for {user_id}: {e}")
                daily_picks_used = 0
            
            daily_picks_remaining = daily_limit - daily_picks_used
            
            return {
                "accessible": True,
                "user_tier": normalized_tier,
                "daily_picks_used": daily_picks_used,
                "daily_picks_limit": daily_limit,
                "daily_picks_remaining": daily_picks_remaining,
                "club_100_view_cost": self.CLUB_100_PICK_COST,
                "club_100_follow_cost": 1
            }
            
        except Exception as e:
            logger.error(f"Error checking Club 100 status: {str(e)}", exc_info=True)
            raise
    
    async def get_club_100_data_with_unlocked_status(self, db: AsyncSession, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get Club 100 data with unlocked status for specific user
        Returns prop_line only if the user has unlocked that specific pick
        
        Returns:
        {
            "nba": [{...player_data without prop_line...}, ...],
            "nfl": [...],
            ...
            "unlocked_picks": ["player_id_1", "player_id_2", ...]
        }
        """
        try:
            # Get all Club 100 data
            all_data = await self.get_club_100_data(db)
            
            # Get user's unlocked picks
            unlocked_picks: List[str] = []
            if user_id:
                try:
                    result = await db.execute(select(User).where(User.id == user_id))
                    user = result.scalar_one_or_none()
                    raw_unlocked = getattr(user, 'club_100_unlocked_picks', None)
                    if isinstance(raw_unlocked, list):
                        unlocked_picks = [cast(str, item) for item in raw_unlocked if isinstance(item, str)]
                except Exception as e:
                    logger.warning(f"Could not get unlocked picks for user {user_id}: {e}")
            
            # Remove prop_line from players that user hasn't unlocked
            filtered_data = {}
            for sport, players in all_data.items():
                filtered_players = []
                for player in players:
                    player_copy = dict(player)
                    player_id = player_copy.get("player_id")
                    
                    # If unlocked, keep prop_line; otherwise remove it
                    if player_id not in unlocked_picks:
                        player_copy.pop("prop_line", None)
                    
                    filtered_players.append(player_copy)
                
                filtered_data[sport] = filtered_players
            
            # Add unlocked picks info
            filtered_data["unlocked_picks"] = unlocked_picks
            
            logger.info(f"[CLUB100] User {user_id} has {len(unlocked_picks)} unlocked picks")
            return filtered_data
            
        except Exception as e:
            logger.error(f"[CLUB100] Error getting Club 100 data with unlocked status: {str(e)}", exc_info=True)
            raise
    
    async def follow_club_100_pick(self, db: AsyncSession, user_id: str, player_id: str) -> Dict[str, Any]:
        """
        Follow/unlock a specific Club 100 pick (costs 1 daily pick)
        
        Returns:
        {
            "success": True,
            "player_id": "nba_LJ_1",
            "prop_line": "Over 24.5 Points",
            ...other player data...
            "pick_cost": 1,
            "message": "Pick unlocked!"
        }
        """
        try:
            # Get the user
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            logger.info(f"[CLUB100] User {user_id} following pick {player_id}")
            
            # Check if already unlocked
            unlocked_picks = getattr(user, 'club_100_unlocked_picks', []) if isinstance(getattr(user, 'club_100_unlocked_picks', []), list) else []
            if player_id in unlocked_picks:
                raise ValueError(f"Player {player_id} already unlocked")
            
            # Find the player data
            try:
                all_data = await self.get_club_100_data(db)
            except Exception as e:
                logger.warning(f"[CLUB100] Primary Club 100 data fetch failed during follow; using DB-only fallback: {e}", exc_info=True)
                all_data = await self.get_club_100_data_from_db(db)

            player_data = None
            for sport_players in all_data.values():
                for player in sport_players:
                    if player.get("player_id") == player_id:
                        player_data = player
                        break
                if player_data:
                    break
            
            if not player_data:
                raise ValueError(f"Player {player_id} not found in Club 100 data")
            
            # Add player_id to unlocked list
            unlocked_picks.append(player_id)
            user_obj = cast(Any, user)
            setattr(user_obj, 'club_100_unlocked_picks', unlocked_picks)
            
            # Save user changes
            db.add(user)
            await db.commit()
            
            # Record the prediction in database for metrics tracking
            # This ensures individual Club 100 unlocks appear in platform metrics
            try:
                from app.models.db_models import Prediction, user_predictions
                from sqlalchemy import insert
                from datetime import datetime
                
                # Create a Prediction record for this Club 100 player follow
                # sport='club_100' (NOT 'club_100_access') so it appears in metrics
                pred_id = f"club_100_follow_{user_id}_{player_id}_{datetime.utcnow().timestamp()}"
                pred = Prediction(
                    id=pred_id,
                    sport='club_100',  # Regular Club 100 pick (appears in metrics)
                    league='club_100',
                    prediction=f"{player_data.get('name', 'Player')} - {player_data.get('prop_line', 'Club 100')}",
                    confidence=0.85,  # Moderate confidence for Club 100 picks
                    prediction_type='player_prop',
                    player=player_data.get('name'),
                    market_key=player_data.get('prop_line'),
                    event_id=player_id,
                    sport_key='club_100',
                    is_club_100_pick=True,  # Mark as Club 100 pick for metrics tracking
                    created_at=datetime.utcnow()
                )
                db.add(pred)
                await db.commit()
                
                # Add to user_predictions to record the follow
                ins_stmt = insert(user_predictions).values(
                    user_id=user_id,
                    prediction_id=pred_id,
                    created_at=datetime.utcnow()
                )
                await db.execute(ins_stmt)
                await db.commit()
                
                # Record in PredictionRecord for accuracy history
                try:
                    from app.services.prediction_history_service import PredictionHistoryService
                    history_service = PredictionHistoryService(db)
                    await history_service.record_prediction(
                        user_id=user_id,
                        sport_key='club_100',
                        event_id=player_id,
                        prediction_data={
                            'prediction': f"{player_data.get('name', 'Player')} - {player_data.get('prop_line', 'Club 100')}",
                            'confidence': 85,  # As percentage for history
                            'prediction_type': 'player_prop',
                            'player_name': player_data.get('name'),
                            'matchup': 'Club 100 Pick',
                            'stat_type': player_data.get('prop_line')
                        }
                    )
                except Exception as history_err:
                    logger.warning(f"[CLUB100] Failed to record in prediction history: {history_err}")
                
                logger.info(f"[CLUB100] Recorded Club 100 pick in metrics for player {player_id}")
            except Exception as tracking_err:
                logger.warning(f"[CLUB100] Failed to record prediction for metrics: {tracking_err}")
                # Don't fail the unlock if tracking fails
            
            logger.info(f"[CLUB100] Player {player_id} unlocked for user {user_id}")
            
            return {
                "success": True,
                "player_id": player_id,
                "unlocked": True,
                **player_data,  # Include all player data including prop_line
                "pick_cost": 1,
                "message": f"Unlocked {player_data.get('name', 'Player')}! Now following this prop line."
            }
            
        except Exception as e:
            logger.error(f"[CLUB100] Error following Club 100 pick {player_id} for user {user_id}: {str(e)}", exc_info=True)
            raise


# Shared Club 100 service instance used by route handlers for caching and reduced ESPN load
club_100_service = Club100Service()
