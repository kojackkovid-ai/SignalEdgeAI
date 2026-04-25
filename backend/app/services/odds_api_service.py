import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

from app.config import settings

class OddsApiService:
    def __init__(self):
        self.api_keys = settings.odds_api_keys
        if self.api_keys:
            logger.info(f"OddsApiService initialized with {len(self.api_keys)} odds API key(s).")
        else:
            logger.warning("OddsApiService initialized with no Odds API keys configured.")

        self.base_url = getattr(settings, "odds_api_base_url", "https://api.the-odds-api.com/v4").rstrip("/")
        self.timeout = 10
        # Simple in-memory cache to prevent over-fetching from external API
        # Key: sport_key (or 'all_predictions'), Value: (timestamp, data)
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes cache TTL

    async def _call_odds_api(self, endpoint: str, params: Dict[str, Any]) -> Optional[Any]:
        if not self.api_keys:
            logger.warning("No OddsAPI keys configured. Skipping OddsAPI request to %s", endpoint)
            return None

        last_error = None
        for index, api_key in enumerate(self.api_keys, start=1):
            params["apiKey"] = api_key
            url = f"{self.base_url}{endpoint}"
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, params=params, timeout=self.timeout)
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status in (401, 403, 429, 503):
                    logger.warning(
                        "OddsAPI key %d/%d returned %d for %s. Trying next key.",
                        index,
                        len(self.api_keys),
                        status,
                        endpoint,
                    )
                    last_error = e
                    continue
                logger.error(
                    "Error fetching %s from OddsAPI: HTTP %d - %s",
                    endpoint,
                    status,
                    e.response.text,
                )
                return None
            except httpx.TimeoutException as e:
                logger.error("Timeout fetching %s from OddsAPI: %s", endpoint, str(e))
                last_error = e
                continue
            except Exception as e:
                logger.error(
                    "Error fetching %s from OddsAPI: %s - %s",
                    endpoint,
                    type(e).__name__,
                    str(e),
                    exc_info=True,
                )
                last_error = e
                continue

        if last_error is not None:
            logger.error(
                "All OddsAPI keys exhausted for %s. Last error: %s",
                endpoint,
                str(last_error),
            )
        return None

    async def get_sports(self) -> List[Dict[str, Any]]:
        """Get list of available sports"""
        data = await self._call_odds_api("/sports", {})
        return data or []

    async def get_events(self, sport_key: str) -> List[Dict[str, Any]]:
        """Get events with odds for a specific sport"""
        # Check cache
        import time
        current_time = time.time()
        cache_key = f"events_{sport_key}"

        if cache_key in self._cache:
            ts, data = self._cache[cache_key]
            if current_time - ts < self._cache_ttl:
                return data

        params = {
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "american",
        }
        data = await self._call_odds_api(f"/sports/{sport_key}/odds", params)
        if data:
            self._cache[cache_key] = (current_time, data)
            return data
        return []

    async def get_event_odds(self, sport_key: str, event_id: str, markets: str) -> Optional[Dict[str, Any]]:
        """Get odds for a specific event with specified markets"""
        params = {
            "regions": "us",
            "markets": markets,
            "oddsFormat": "american",
        }
        return await self._call_odds_api(
            f"/sports/{sport_key}/events/{event_id}/odds",
            params,
        )

    async def get_odds_for_game(self, sport_key: str, event_id: str, home_team: Optional[str] = None, away_team: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get odds for a specific game.
        If home_team and away_team are provided, attempts to find the event by matching names
        instead of using event_id (which is likely from a different source like ESPN).
        """
        logger.info(f"get_odds_for_game called with sport_key={sport_key}, event_id={event_id}, home_team={home_team}, away_team={away_team}")
        
        if not home_team or not away_team:
            logger.warning(f"Missing team names - falling back to ID lookup for event_id={event_id}")
            # Fallback to direct ID lookup if names not provided
            markets = "h2h,spreads,totals"
            result = await self.get_event_odds(sport_key, event_id, markets)
            logger.info(f"ID lookup result: {'Found' if result else 'Not found'}")
            return result
        
        # Fetch all active events for the sport
        logger.info(f"Fetching events for sport_key={sport_key} to match teams")
        events = await self.get_events(sport_key)
        logger.info(f"Found {len(events)} events for sport_key={sport_key}")
        
        # Helper for normalizing names
        def normalize(name):
            return name.lower().replace('.', '').replace(' city', '').replace(' st', ' state').strip()
            
        norm_home = normalize(home_team)
        norm_away = normalize(away_team)
        logger.info(f"Normalized teams - home: '{norm_home}', away: '{norm_away}'")
        
        for event in events:
            # Check if names match
            evt_home = normalize(event.get('home_team', ''))
            evt_away = normalize(event.get('away_team', ''))
            
            logger.debug(f"Checking event: home_team='{evt_home}' vs '{norm_home}', away_team='{evt_away}' vs '{norm_away}'")
            
            # Check for exact match or containment
            # e.g. "Lakers" in "Los Angeles Lakers"
            match_home = norm_home in evt_home or evt_home in norm_home
            match_away = norm_away in evt_away or evt_away in norm_away
            
            logger.debug(f"Match results - home: {match_home}, away: {match_away}")
            
            if match_home and match_away:
                logger.info(f"SUCCESS: Found matching event for {home_team} vs {away_team}")
                return event
                
        logger.warning(f"NO MATCH: Could not find event for {home_team} vs {away_team} in {len(events)} events")
        return None

    async def get_player_props(self, sport_key: str, event_id: str) -> List[Dict[str, Any]]:
        """Get player props for an event"""
        try:
            # Determine relevant markets based on sport
            markets = []
            if "nba" in sport_key.lower():
                markets = ["player_points", "player_rebounds", "player_assists"]
            elif "nfl" in sport_key.lower():
                markets = ["player_pass_tds", "player_rush_yds", "player_rec_yds"]
            elif "nhl" in sport_key.lower():
                markets = ["player_points", "player_assists"]
            else:
                return [] # No props for other sports yet

            market_str = ",".join(markets)
            data = await self.get_event_odds(sport_key, event_id, market_str)
            
            if not data:
                return []

            # Extract Event Info
            home_team = data.get("home_team", "Unknown")
            away_team = data.get("away_team", "Unknown")
            commence_time = data.get("commence_time", datetime.utcnow().isoformat())
            
            # Format time
            try:
                from datetime import timedelta
                game_time_dt = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                game_time_et = game_time_dt - timedelta(hours=5)
                game_time_display = game_time_et.strftime("%b %d, %I:%M %p ET")
            except:
                game_time_display = "TBD"

            # Map sport/league
            sport_map = {
                "americanfootball_nfl": ("NFL", "NFL"),
                "basketball_nba": ("NBA", "NBA"),
                "icehockey_nhl": ("NHL", "NHL"),
                "soccer_epl": ("Soccer", "EPL"),
                "soccer_usa_mls": ("Soccer", "MLS")
            }
            sport_display, league_display = sport_map.get(sport_key, ("Unknown", "Unknown"))

            # Transform to predictions
            from app.services.ml_service import MLService
            ml_service = MLService()
            
            props = []
            bookmakers = data.get("bookmakers", [])
            if not bookmakers:
                return []
                
            # Use a map to track unique props across bookmakers
            # Key: {player}_{market_key}_{point}
            seen_props = set()
            
            # Iterate through all bookmakers to find the best props
            for bk in bookmakers:
                for market in bk.get("markets", []):
                    key = market.get("key")
                    outcomes = market.get("outcomes", [])
                    
                    # Group by player and point to ensure we compare Over vs Under for the same line
                    grouped_outcomes = {}
                    for outcome in outcomes:
                        # Correctly extract player name
                        # OddsAPI often puts player name in 'description' for Over/Under markets
                        player = outcome.get("description")
                        if not player:
                            player = outcome.get("name")
                            
                        # If name is Over/Under, and no description, we might have an issue, 
                        # but usually description contains the player name.
                        
                        point = outcome.get("point")
                        if not player: continue
                        
                        # Create unique key for this specific prop line
                        k = f"{player}_{point}"
                        if k not in grouped_outcomes:
                            grouped_outcomes[k] = []
                        grouped_outcomes[k].append(outcome)
                        
                    for k, outcome_pair in grouped_outcomes.items():
                        # Unique identifier for this prop scenario
                        unique_key = f"{key}_{k}"
                        if unique_key in seen_props:
                            continue
                            
                        # Calculate best pick from the pair (Over vs Under)
                        pred = await ml_service.predict_prop_from_market(key, outcome_pair)
                        if pred:
                            seen_props.add(unique_key)
                            
                            # Format odds as string for Pydantic validation
                            odds_val = pred.get("odds")
                            odds_str = str(odds_val)
                            if isinstance(odds_val, (int, float)) and odds_val > 0:
                                odds_str = f"+{odds_val}"
                            
                            props.append({
                                **pred,
                                "id": f"{event_id}_{key}_{k}", # Unique ID for this prop prediction
                                "market_key": key,
                                "player": outcome_pair[0].get("description") or outcome_pair[0].get("name"),
                                "point": outcome_pair[0].get("point"),
                                "sport_key": sport_key,
                                "event_id": event_id,
                                "sport": sport_display,
                                "league": league_display,
                                "matchup": f"{away_team} @ {home_team}",
                                "game_time": game_time_display,
                                "prediction_type": "player_prop",
                                "created_at": datetime.utcnow().isoformat() + "Z",
                                "odds": odds_str
                            })
            
            return props

        except Exception as e:
            logger.error(f"Error getting player props: {e}")
            return []

    async def get_all_upcoming_events(self, sport: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get upcoming events for supported sports only"""
        try:
            # ONLY fetch supported sports to save API credits
            supported_sports = {
                "americanfootball_nfl": "nfl",
                "basketball_nba": "nba",
                "basketball_ncaa": "ncaab",
                "icehockey_nhl": "nhl",
                "soccer_epl": "soccer",
                "soccer_usa_mls": "soccer"
            }
            
            all_events = {}
            
            for sport_key, display_name in supported_sports.items():
                # Filter by sport if provided
                if sport and sport.lower() not in display_name.lower() and sport.lower() not in sport_key.lower():
                    continue

                events = await self.get_events(sport_key)
                if events:
                    # Limit to 4 events per sport to save API credits
                    all_events[sport_key] = events[:4]
                    logger.info(f"Fetched {len(events[:4])} events for {sport_key}")
            
            return all_events
        except Exception as e:
            logger.error(f"Error fetching all events: {type(e).__name__} - {str(e)}", exc_info=True)
            return {}

    async def transform_event_to_prediction(self, event: Dict[str, Any], sport_key: str) -> Optional[Dict[str, Any]]:
        """Transform OddsAPI event into prediction format using real ML/Odds data"""
        try:
            from app.services.ml_service import MLService
            ml_service = MLService()
            
            home_team = event.get("home_team", "Unknown")
            away_team = event.get("away_team", "Unknown")
            commence_time = event.get("commence_time", datetime.utcnow().isoformat())
            
            # Parse commence time for display
            try:
                from datetime import timedelta
                game_time = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                # Convert to ET (UTC-5)
                game_time_et = game_time - timedelta(hours=5)
                game_time_display = game_time_et.strftime("%b %d, %I:%M %p ET")
            except:
                game_time_display = "TBD"
            
            # Get real prediction from ML Service (based on implied probability)
            ml_pred = await ml_service.predict_from_odds(event)
            
            if not ml_pred:
                # If we can't make a valid prediction from odds, skip this event
                return None
                
            # Format sport name properly
            sport_map = {
                "americanfootball_nfl": ("NFL", "NFL"),
                "basketball_nba": ("NBA", "NBA"),
                "basketball_ncaa": ("NCAAB", "NCAA"),
                "icehockey_nhl": ("NHL", "NHL"),
                "soccer_epl": ("Soccer", "EPL"),
                "soccer_usa_mls": ("Soccer", "MLS")
            }
            sport_display, league_display = sport_map.get(sport_key, ("Unknown", "Unknown"))
            
            # Get the best available odds for display
            bookmakers = event.get("bookmakers", [])
            odds_display = "-110"
            spread_str = ""
            total_str = ""
            
            if bookmakers:
                markets = bookmakers[0].get("markets", [])
                h2h = next((m for m in markets if m["key"] == "h2h"), None)
                if h2h and h2h.get("outcomes"):
                    # Find the odds for the predicted team
                    pred_team = ml_pred["prediction"].replace(" Win", "")
                    outcome = next((o for o in h2h["outcomes"] if o["name"] == pred_team), None)
                    if outcome:
                        p = outcome.get("price")
                        odds_display = f"{p:+d}" if p else "-110"
                
                # Extract Spread info
                spread_market = next((m for m in markets if m["key"] == "spreads"), None)
                if spread_market:
                    outcomes = spread_market.get("outcomes", [])
                    if len(outcomes) >= 2:
                        s1 = outcomes[0]
                        s2 = outcomes[1]
                        spread_str = f"{s1['name']} {s1['point']} ({s1['price']}) / {s2['name']} {s2['point']} ({s2['price']})"
                
                # Extract Total info
                total_market = next((m for m in markets if m["key"] == "totals"), None)
                if total_market:
                    outcomes = total_market.get("outcomes", [])
                    if outcomes:
                        t = outcomes[0] # Usually first one has the point
                        total_str = f"O/U {t['point']}"

            # Add context to reasoning
            if spread_str:
                ml_pred["reasoning"].append({
                    "factor": "Spread Line",
                    "impact": "Neutral",
                    "weight": 0.1,
                    "explanation": spread_str
                })
            if total_str:
                ml_pred["reasoning"].append({
                    "factor": "Total Line",
                    "impact": "Neutral",
                    "weight": 0.1,
                    "explanation": total_str
                })

            return {
                "id": f"{sport_key}_{event.get('id', '')}",
                "sport_key": sport_key,
                "event_id": event.get('id', ''),
                "sport": sport_display,
                "league": league_display,
                "matchup": f"{away_team} @ {home_team}",
                "game_time": game_time_display,
                "prediction": ml_pred["prediction"],
                "confidence": ml_pred["confidence"],
                "odds": odds_display,
                "prediction_type": ml_pred["prediction_type"],
                "reasoning": ml_pred["reasoning"],
                "models": [], # No fake model breakdown for now
                "created_at": datetime.utcnow().isoformat() + "Z",
                "resolved_at": None,
                "result": None
            }
        except Exception as e:
            logger.error(f"Error transforming event: {type(e).__name__} - {str(e)}", exc_info=True)
            return None

    async def get_predictions(self, sport: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all upcoming events and transform to predictions (4 per sport max)"""
        try:
            # Check cache first
            import time
            current_time = time.time()
            cache_key = f"all_predictions_{sport}" if sport else "all_predictions"
            
            if cache_key in self._cache:
                timestamp, cached_data = self._cache[cache_key]
                if current_time - timestamp < self._cache_ttl:
                    logger.info(f"Returning cached predictions for {cache_key} ({len(cached_data)} items) - Age: {int(current_time - timestamp)}s")
                    return cached_data

            all_events = await self.get_all_upcoming_events(sport=sport)
            if not all_events:
                logger.warning(f"No events found for sport: {sport}")
                return []
                
            predictions = []
            
            for sport_key, events in all_events.items():
                # Get up to 4 predictions per sport to save API credits
                for event in events[:4]:
                    prediction = await self.transform_event_to_prediction(event, sport_key)
                    if prediction:
                        predictions.append(prediction)
            
            logger.info(f"Generated {len(predictions)} predictions from OddsAPI")
            
            # Save to cache
            self._cache[cache_key] = (current_time, predictions)
            
            return predictions
        except Exception as e:
            logger.error(f"Error getting predictions: {type(e).__name__} - {str(e)}", exc_info=True)
            return []
