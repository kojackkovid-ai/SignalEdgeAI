"""
LinesMate.io Web Scraper Service
Scrapes detailed player stats, schedules, last 10 games, and prop lines from LinesMate.io
Provides free access to comprehensive player prop data without API costs
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
import asyncio
from app.cache import cache_manager

logger = logging.getLogger(__name__)

class LinesMateScraper:
    """
    Web scraper to fetch player stats and prop data from LinesMate.io
    LinesMate provides free access to:
    - Season statistics for all players
    - Last 10 games performance
    - Upcoming schedules
    - Player prop lines from multiple sportsbooks
    - Vegas lines and betting consensus
    """
    
    def __init__(self):
        self.base_url = "https://www.linesmate.io"
        self.timeout = 20
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self._cache = {}
        self._cache_ttl = 1800  # 30 minutes cache for stats (longer than odds)
        
        logger.info("LinesMateScraper initialized")
    
    async def get_player_stats(
        self,
        player_name: str,
        sport: str
    ) -> Optional[Dict[str, Any]]:
        """
        Scrape season stats and last 10 games for a player
        
        Args:
            player_name: Player name (e.g., "LeBron James")
            sport: Sport (nba, nfl, mlb, nhl)
        
        Returns:
            Dict with season stats, last 10 game performance, career stats
        """
        try:
            # Check cache first
            import time
            current_time = time.time()
            cache_key = f"linesmate_player:{sport}:{player_name}"
            
            if cache_key in self._cache:
                ts, data = self._cache[cache_key]
                if current_time - ts < self._cache_ttl:
                    logger.info(f"[LINESMATE] Returning cached stats for {player_name}")
                    return data
            
            logger.info(f"[LINESMATE] Fetching stats for {player_name} ({sport})")
            
            # Build search URL
            url = f"{self.base_url}/search"
            params = {
                "q": player_name,
                "sport": sport,
                "type": "player"
            }
            
            headers = {"User-Agent": self.user_agent}
            
            async with httpx.AsyncClient() as client:
                # Search for player
                response = await client.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                    follow_redirects=True
                )
                
                if response.status_code != 200:
                    logger.warning(f"[LINESMATE] Search returned {response.status_code}")
                    return None
                
                # Parse search results
                soup = BeautifulSoup(response.text, 'html.parser')
                player_link = soup.find('a', {'class': 'player-link'})
                
                if not player_link:
                    logger.warning(f"[LINESMATE] Player not found: {player_name}")
                    return None
                
                # Get player profile URL
                player_url = player_link.get('href')
                if not player_url.startswith('http'):
                    player_url = f"{self.base_url}{player_url}"
                
                # Fetch player profile page
                profile_response = await client.get(
                    player_url,
                    headers=headers,
                    timeout=self.timeout
                )
                
                if profile_response.status_code != 200:
                    logger.warning(f"[LINESMATE] Profile fetch returned {profile_response.status_code}")
                    return None
                
                # Parse player stats
                stats = self._parse_player_profile(profile_response.text, sport)
                
                if stats:
                    # Cache the stats
                    self._cache[cache_key] = (current_time, stats)
                    logger.info(f"[LINESMATE] Successfully scraped stats for {player_name}")
                
                return stats
                
        except httpx.TimeoutException as e:
            logger.error(f"[LINESMATE] Timeout fetching player {player_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"[LINESMATE] Error fetching player stats: {e}")
            return None
    
    def _parse_player_profile(self, html: str, sport: str) -> Optional[Dict[str, Any]]:
        """
        Parse HTML from player profile page
        Extracts season stats, recent performance, and player info
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            stats = {
                'player_name': None,
                'team': None,
                'position': None,
                'sport': sport,
                'season_stats': {},
                'last_10_games': [],
                'career_stats': {},
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Extract player name
            name_elem = soup.find('h1', {'class': 'player-name'})
            if name_elem:
                stats['player_name'] = name_elem.text.strip()
            
            # Extract team
            team_elem = soup.find('span', {'class': 'team'})
            if team_elem:
                stats['team'] = team_elem.text.strip()
            
            # Extract position
            pos_elem = soup.find('span', {'class': 'position'})
            if pos_elem:
                stats['position'] = pos_elem.text.strip()
            
            # Extract season stats table
            season_table = soup.find('table', {'class': 'season-stats'})
            if season_table:
                stats['season_stats'] = self._parse_stats_table(season_table)
            
            # Extract last 10 games
            recent_table = soup.find('table', {'class': ['recent-games', 'last-10']})
            if recent_table:
                stats['last_10_games'] = self._parse_game_log(recent_table)
            
            # Extract career stats
            career_table = soup.find('table', {'class': 'career-stats'})
            if career_table:
                stats['career_stats'] = self._parse_stats_table(career_table)
            
            return stats if stats['season_stats'] else None
            
        except Exception as e:
            logger.error(f"[LINESMATE] Error parsing player profile: {e}")
            return None
    
    def _parse_stats_table(self, table) -> Dict[str, Any]:
        """Parse HTML table with player statistics"""
        try:
            stats = {}
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    stat_name = cells[0].text.strip()
                    stat_value = cells[1].text.strip()
                    
                    # Try to convert to float
                    try:
                        stat_value = float(stat_value)
                    except ValueError:
                        pass
                    
                    stats[stat_name.lower().replace(' ', '_')] = stat_value
            
            return stats
        except Exception as e:
            logger.error(f"[LINESMATE] Error parsing stats table: {e}")
            return {}
    
    def _parse_game_log(self, table) -> List[Dict[str, Any]]:
        """Parse game log table with last 10 games performance"""
        try:
            games = []
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 5:
                    game = {
                        'date': cells[0].text.strip(),
                        'opponent': cells[1].text.strip(),
                        'result': cells[2].text.strip(),  # W/L
                        'points': self._extract_number(cells[3].text),
                        'rebounds': self._extract_number(cells[4].text) if len(cells) > 4 else None,
                        'assists': self._extract_number(cells[5].text) if len(cells) > 5 else None,
                    }
                    games.append(game)
            
            return games
        except Exception as e:
            logger.error(f"[LINESMATE] Error parsing game log: {e}")
            return []
    
    async def get_player_prop_lines(
        self,
        player_name: str,
        sport: str,
        prop_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch player prop lines and consensus from LinesMate
        
        Args:
            player_name: Player name
            sport: Sport (nba, nfl, mlb, nhl)
            prop_type: Type of prop (points, rebounds, assists, etc.)
        
        Returns:
            Dict with line, over/under odds from multiple books
        """
        try:
            logger.info(f"[LINESMATE] Fetching {prop_type} lines for {player_name}")
            
            # Build props page URL
            url = f"{self.base_url}/{sport}/props"
            params = {
                "player": player_name,
                "prop": prop_type
            }
            
            headers = {"User-Agent": self.user_agent}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                    follow_redirects=True
                )
                
                if response.status_code != 200:
                    logger.warning(f"[LINESMATE] Props page returned {response.status_code}")
                    return None
                
                # Parse props page
                lines = self._parse_props_page(response.text, player_name, prop_type)
                logger.info(f"[LINESMATE] Found lines for {player_name} {prop_type}")
                
                return lines
                
        except Exception as e:
            logger.error(f"[LINESMATE] Error fetching prop lines: {e}")
            return None
    
    def _parse_props_page(self, html: str, player_name: str, prop_type: str) -> Optional[Dict[str, Any]]:
        """Parse props page for specific player prop"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find the prop row for this player
            prop_rows = soup.find_all('tr', {'class': 'prop-row'})
            
            for row in prop_rows:
                # Check if this is the right player/prop
                player_cell = row.find('td', {'class': 'player-name'})
                if player_cell and player_name.lower() in player_cell.text.lower():
                    
                    # Find prop type in this row
                    prop_cell = row.find('td', {'class': 'prop-type'})
                    if prop_cell and prop_type.lower() in prop_cell.text.lower():
                        
                        # Extract line and odds
                        return self._extract_prop_data(row)
            
            logger.warning(f"[LINESMATE] Prop row not found for {player_name} {prop_type}")
            return None
            
        except Exception as e:
            logger.error(f"[LINESMATE] Error parsing props page: {e}")
            return None
    
    def _extract_prop_data(self, row) -> Dict[str, Any]:
        """Extract line and odds from prop row"""
        try:
            prop_data = {
                'line': None,
                'over_odds': {},
                'under_odds': {},
                'consensus_line': None,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Extract consensus line
            line_cell = row.find('td', {'class': 'consensus-line'})
            if line_cell:
                line_text = line_cell.text.strip()
                prop_data['line'] = self._extract_number(line_text)
                prop_data['consensus_line'] = prop_data['line']
            
            # Extract odds from different sportsbooks
            odds_cells = row.find_all('td', {'class': 'sportsbook-odds'})
            for cell in odds_cells:
                book_name = cell.get('data-book', 'unknown')
                
                # Parse over/under odds
                over = cell.find('span', {'class': 'over-odds'})
                under = cell.find('span', {'class': 'under-odds'})
                
                if over:
                    prop_data['over_odds'][book_name] = self._extract_number(over.text)
                if under:
                    prop_data['under_odds'][book_name] = self._extract_number(under.text)
            
            return prop_data
            
        except Exception as e:
            logger.error(f"[LINESMATE] Error extracting prop data: {e}")
            return {}
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract numeric value from text"""
        try:
            # Remove common non-numeric characters except . and -
            cleaned = re.sub(r'[^\d.-]', '', text.strip())
            if cleaned:
                return float(cleaned)
        except (ValueError, AttributeError):
            pass
        return None
    
    async def get_schedule(
        self,
        sport: str,
        days_ahead: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Fetch upcoming schedule from LinesMate
        
        Args:
            sport: Sport (nba, nfl, mlb, nhl)
            days_ahead: How many days ahead to fetch
        
        Returns:
            List of upcoming games
        """
        try:
            logger.info(f"[LINESMATE] Fetching {sport} schedule for next {days_ahead} days")
            
            url = f"{self.base_url}/{sport}/schedule"
            params = {
                "days": days_ahead
            }
            
            headers = {"User-Agent": self.user_agent}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                    follow_redirects=True
                )
                
                if response.status_code != 200:
                    logger.warning(f"[LINESMATE] Schedule fetch returned {response.status_code}")
                    return []
                
                games = self._parse_schedule(response.text)
                logger.info(f"[LINESMATE] Found {len(games)} upcoming games")
                
                return games
                
        except Exception as e:
            logger.error(f"[LINESMATE] Error fetching schedule: {e}")
            return []
    
    def _parse_schedule(self, html: str) -> List[Dict[str, Any]]:
        """Parse schedule table"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            games = []
            
            game_rows = soup.find_all('tr', {'class': 'game-row'})
            
            for row in game_rows:
                try:
                    game = {
                        'date': row.find('td', {'class': 'date'}).text.strip(),
                        'time': row.find('td', {'class': 'time'}).text.strip(),
                        'away_team': row.find('td', {'class': 'away-team'}).text.strip(),
                        'home_team': row.find('td', {'class': 'home-team'}).text.strip(),
                        'spread': self._extract_number(row.find('td', {'class': 'spread'}).text),
                        'total': self._extract_number(row.find('td', {'class': 'total'}).text),
                    }
                    games.append(game)
                except AttributeError:
                    continue
            
            return games
        except Exception as e:
            logger.error(f"[LINESMATE] Error parsing schedule: {e}")
            return []
    
    async def get_team_schedule(
        self,
        team_name: str,
        sport: str
    ) -> List[Dict[str, Any]]:
        """
        Get schedule for a specific team
        """
        try:
            logger.info(f"[LINESMATE] Fetching {team_name} schedule")
            
            url = f"{self.base_url}/{sport}/schedule"
            params = {"team": team_name}
            
            headers = {"User-Agent": self.user_agent}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                    follow_redirects=True
                )
                
                if response.status_code != 200:
                    return []
                
                return self._parse_schedule(response.text)
                
        except Exception as e:
            logger.error(f"[LINESMATE] Error fetching team schedule: {e}")
            return []
    
    def clear_cache(self):
        """Clear all cached data"""
        self._cache.clear()
        logger.info("[LINESMATE] Cache cleared")
