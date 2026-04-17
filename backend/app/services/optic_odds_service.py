"""
OpticOdds API Service
Fetches real player props lines and odds data from OpticOdds
Used to enhance player prop predictions with actual market data
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.config import settings
import asyncio
import json

logger = logging.getLogger(__name__)

class OpticOddsService:
    """
    Service to fetch player props and lines from OpticOdds API
    OpticOdds provides real-time player props, odds, and lines from multiple sportsbooks
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'optic_odds_api_key', None)
        self.base_url = "https://api.opticodds.com/v2"
        self.timeout = 15
        self._cache = {}
        self._cache_ttl = 600  # 10 minutes cache
        
        if not self.api_key:
            logger.warning("OpticOdds API key not configured. Player props will use ESPN data only.")
        else:
            logger.info(f"OpticOddsService initialized with API key: {self.api_key[:5]}...")
    
    async def get_player_props(
        self,
        sport: str,
        event_id: Optional[str] = None,
        player_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get player props from OpticOdds
        
        Args:
            sport: Sport code (nba, nfl, mlb, nhl)
            event_id: Optional ESPN/OpticOdds event ID
            player_name: Optional player name to filter
        
        Returns:
            List of player props with lines, odds, and sportsbook data
        """
        if not self.api_key:
            logger.warning("OpticOdds API key not configured")
            return []
        
        try:
            # Map ESPN sport keys to OpticOdds sport codes
            sport_mapping = {
                'basketball_nba': 'NBA',
                'basketball_ncaab': 'NCAAB',
                'football_nfl': 'NFL',
                'football_ncaaf': 'NCAAF',
                'baseball_mlb': 'MLB',
                'hockey_nhl': 'NHL',
                'soccer_epl': 'SOCCER',
                'soccer_mls': 'SOCCER'
            }
            
            optic_sport = sport_mapping.get(sport)
            if not optic_sport:
                logger.warning(f"Unsupported sport for OpticOdds: {sport}")
                return []
            
            # Build cache key
            cache_key = f"optic_props:{sport}:{event_id or 'all'}:{player_name or 'all'}"
            
            # Check cache
            import time
            current_time = time.time()
            if cache_key in self._cache:
                ts, data = self._cache[cache_key]
                if current_time - ts < self._cache_ttl:
                    logger.info(f"[OPTIC_ODDS] Returning cached data for {sport}")
                    return data
            
            # Fetch from API
            params = {
                "apiKey": self.api_key,
                "sport": optic_sport,
                "markets": "player_props",
                "includeOdds": "true"
            }
            
            if event_id:
                params["eventId"] = event_id
            
            if player_name:
                params["playerName"] = player_name
            
            url = f"{self.base_url}/props"
            
            logger.info(f"[OPTIC_ODDS] Fetching props from {url} for {sport}")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    props = data.get("props", [])
                    
                    # Update cache
                    self._cache[cache_key] = (current_time, props)
                    
                    logger.info(f"[OPTIC_ODDS] Successfully fetched {len(props)} props for {sport}")
                    return props
                elif response.status_code == 401:
                    logger.error("[OPTIC_ODDS] Unauthorized - invalid API key")
                    return []
                elif response.status_code == 404:
                    logger.warning(f"[OPTIC_ODDS] No props found for {sport}")
                    return []
                else:
                    logger.error(f"[OPTIC_ODDS] API error {response.status_code}: {response.text}")
                    return []
                    
        except httpx.TimeoutException as e:
            logger.error(f"[OPTIC_ODDS] Timeout fetching props: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"[OPTIC_ODDS] Error fetching props: {type(e).__name__}: {e}")
            return []
    
    async def get_player_prop_lines(
        self,
        sport: str,
        player_name: str,
        prop_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get specific player prop lines
        
        Args:
            sport: Sport code
            player_name: Player name
            prop_type: Type of prop (e.g., 'points', 'rebounds', 'assists', 'passing_yards', etc.)
        
        Returns:
            Dict with lines, odds, and sportsbook data from multiple books
        """
        try:
            props = await self.get_player_props(sport, player_name=player_name)
            
            # Filter to matching prop type
            for prop in props:
                if prop.get('prop_type', '').lower() == prop_type.lower():
                    return self._enrich_prop_data(prop)
            
            logger.warning(f"[OPTIC_ODDS] No prop found for {player_name} - {prop_type}")
            return None
            
        except Exception as e:
            logger.error(f"[OPTIC_ODDS] Error getting prop lines: {e}")
            return None
    
    async def get_all_player_props_for_event(
        self,
        sport: str,
        event_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all player props for a specific event/game
        
        Returns:
            List of enriched player props
        """
        try:
            props = await self.get_player_props(sport, event_id=event_id)
            return [self._enrich_prop_data(p) for p in props]
        except Exception as e:
            logger.error(f"[OPTIC_ODDS] Error getting event props: {e}")
            return []
    
    def _enrich_prop_data(self, prop: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich prop data with additional useful information
        """
        try:
            # Extract best odds from all sportsbooks
            best_over = None
            best_under = None
            best_over_book = None
            best_under_book = None
            
            odds_data = prop.get('odds', {})
            if isinstance(odds_data, dict):
                for book_name, book_odds in odds_data.items():
                    if isinstance(book_odds, dict):
                        over_odds = book_odds.get('over_odds')
                        under_odds = book_odds.get('under_odds')
                        
                        if over_odds and (best_over is None or over_odds > best_over):
                            best_over = over_odds
                            best_over_book = book_name
                        
                        if under_odds and (best_under is None or under_odds > best_under):
                            best_under = under_odds
                            best_under_book = book_name
            
            # Add consensus data
            consensus_line = prop.get('consensus_line')
            if consensus_line is None and prop.get('line'):
                consensus_line = float(prop.get('line', 0))
            
            return {
                'player_name': prop.get('player_name', 'Unknown'),
                'player_id': prop.get('player_id'),
                'prop_type': prop.get('prop_type', 'unknown'),
                'display_name': prop.get('display_name', prop.get('prop_type', 'Unknown')),
                'line': prop.get('line'),
                'consensus_line': consensus_line,
                'over_odds': best_over,
                'under_odds': best_under,
                'best_over_book': best_over_book,
                'best_under_book': best_under_book,
                'updated_at': prop.get('updated_at'),
                'all_odds': prop.get('odds', {}),
                'status': prop.get('status', 'active'),
                'sport': prop.get('sport'),
                'event_id': prop.get('event_id')
            }
        except Exception as e:
            logger.error(f"[OPTIC_ODDS] Error enriching prop data: {e}")
            return prop
    
    async def get_best_odds(
        self,
        sport: str,
        player_name: str,
        prop_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get best available odds from all sportsbooks for a player prop
        
        Returns:
            Dict with best over/under odds and which book provides them
        """
        try:
            prop = await self.get_player_prop_lines(sport, player_name, prop_type)
            
            if not prop:
                return None
            
            return {
                'line': prop.get('line'),
                'best_over_odds': prop.get('over_odds'),
                'best_over_book': prop.get('best_over_book'),
                'best_under_odds': prop.get('under_odds'),
                'best_under_book': prop.get('best_under_book'),
                'all_books': list(prop.get('all_odds', {}).keys())
            }
        except Exception as e:
            logger.error(f"[OPTIC_ODDS] Error getting best odds: {e}")
            return None
    
    async def search_player_props(
        self,
        sport: str,
        player_fragment: str
    ) -> List[Dict[str, Any]]:
        """
        Search for player props by partial player name
        
        Args:
            sport: Sport code
            player_fragment: Partial player name to search for
        
        Returns:
            List of matching player props
        """
        try:
            if not self.api_key:
                return []
            
            params = {
                "apiKey": self.api_key,
                "search": player_fragment,
                "sport": self._map_sport(sport)
            }
            
            url = f"{self.base_url}/props/search"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('results', [])
                else:
                    logger.error(f"[OPTIC_ODDS] Search error {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"[OPTIC_ODDS] Error searching props: {e}")
            return []
    
    def _map_sport(self, sport: str) -> str:
        """Map ESPN sport key to OpticOdds sport code"""
        mapping = {
            'basketball_nba': 'NBA',
            'basketball_ncaab': 'NCAAB',
            'football_nfl': 'NFL',
            'football_ncaaf': 'NCAAF',
            'baseball_mlb': 'MLB',
            'hockey_nhl': 'NHL',
            'soccer_epl': 'SOCCER',
            'soccer_mls': 'SOCCER'
        }
        return mapping.get(sport, sport.upper())
    
    async def health_check(self) -> bool:
        """Check if OpticOdds API is accessible"""
        if not self.api_key:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    params={"apiKey": self.api_key},
                    timeout=5
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"[OPTIC_ODDS] Health check failed: {e}")
            return False
