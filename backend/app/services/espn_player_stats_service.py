"""
ESPN Player Stats Service
Extracts player statistics from ESPN scoreboard API for player props

This service scrapes player stats from the ESPN scoreboard endpoint,
which provides leaders (top performers) for each team in each game.
"""
import asyncio
import httpx
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

class ESPNPlayerStatsService:
    """
    Service to extract player statistics from ESPN APIs.
    
    Key Discovery: The ESPN scoreboard API returns player "leaders" with
    actual game stats - this can be used for player props!
    
    Endpoints that work:
    - /apis/site/v2/sports/basketball/nba/scoreboard - Game scoreboards with leaders
    - /apis/site/v2/sports/basketball/nba/teams/{id}/roster - Team rosters
    """
    
    # Sport to ESPN API path mapping
    SPORT_API_PATHS = {
        'nba': 'basketball/nba',
        'wnba': 'basketball/wnba', 
        'nhl': 'hockey/nhl',
        'mlb': 'baseball/mlb',
        'nfl': 'football/nfl',
    }
    
    # Categories available in scoreboard leaders
    LEADER_CATEGORIES = {
        'nba': ['points', 'rebounds', 'assists', 'steals', 'blocks', 'threePointersMade'],
        'nhl': ['goals', 'assists', 'shotsOnGoal', 'hits', 'blocks', 'plusMinus'],
        'mlb': ['hits', 'homeRuns', 'runsBattedIn', 'stolenBases', 'battingAverage', 'ops'],
    }
    
    def __init__(self):
        self.base_url = "https://site.api.espn.com/apis/site/v2"
        self._player_cache = {}  # Cache for player stats
        self._season_stats = defaultdict(list)  # Season averages
        
    async def get_game_player_stats(self, sport: str, event_id: str = None) -> Dict[str, Any]:
        """
        Get player stats from a specific game scoreboard.
        
        Returns dict with:
        - leaders: list of top performers per category per team
        - team_stats: team-level statistics
        """
        api_path = self.SPORT_API_PATHS.get(sport.lower())
        if not api_path:
            logger.warning(f"Unknown sport: {sport}")
            return {}
            
        if event_id:
            url = f"{self.base_url}/sports/{api_path}/scoreboard?event={event_id}"
        else:
            url = f"{self.base_url}/sports/{api_path}/scoreboard"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    logger.warning(f"Scoreboard API returned {response.status_code}")
                    return {}
                    
                data = response.json()
                return self._parse_scoreboard_data(sport, data)
                
        except Exception as e:
            logger.error(f"Error fetching scoreboard: {e}")
            return {}
    
    async def get_today_games_player_stats(self, sport: str) -> List[Dict[str, Any]]:
        """
        Get player stats from all today's games.
        This is the key method for generating player props!
        """
        api_path = self.SPORT_API_PATHS.get(sport.lower())
        if not api_path:
            return []
            
        url = f"{self.base_url}/sports/{api_path}/scoreboard"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    logger.warning(f"Scoreboard API returned {response.status_code}")
                    return []
                    
                data = response.json()
                games = self._parse_all_games(sport, data)
                if games:
                    await self._attach_scheduled_game_rosters(sport, games)
                return games
                
        except Exception as e:
            logger.error(f"Error fetching today's games: {e}")
            return []
    
    async def get_games_for_date(self, sport: str, date_str: str) -> List[Dict[str, Any]]:
        """
        Get games scheduled for a specific date.
        Date format: YYYYMMDD
        """
        api_path = self.SPORT_API_PATHS.get(sport.lower())
        if not api_path:
            return []
            
        url = f"{self.base_url}/sports/{api_path}/scoreboard?dates={date_str}"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    logger.warning(f"Scoreboard API returned {response.status_code} for date {date_str}")
                    return []
                    
                data = response.json()
                return self._parse_scheduled_games(sport, data)
                
        except Exception as e:
            logger.error(f"Error fetching games for date {date_str}: {e}")
            return []
    
    def _parse_scoreboard_data(self, sport: str, data: Dict) -> Dict[str, Any]:
        """Parse a single game's scoreboard data."""
        result = {
            'game': {},
            'home_team': {},
            'away_team': {},
            'leaders': [],
        }
        
        events = data.get('events', [])
        if not events:
            return result
            
        event = events[0]
        result['game'] = {
            'id': event.get('id'),
            'name': event.get('name'),
            'status': event.get('status', {}).get('type', {}).get('name'),
            'start_date': event.get('date'),
        }
        
        competitions = event.get('competitions', [])
        if not competitions:
            return result
            
        comp = competitions[0]
        competitors = comp.get('competitors', [])
        
        for team in competitors:
            team_info = team.get('team', {})
            team_name = team_info.get('displayName')
            team_abbrev = team_info.get('abbreviation')
            home_away = team.get('homeAway')
            
            team_data = {
                'id': team.get('id'),
                'name': team_name,
                'abbreviation': team_abbrev,
                'home_away': home_away,
                'score': team.get('score'),
                'leaders': [],
                'statistics': [],
            }
            
            # Extract leaders - NOTE: structure is nested!
            # team.get('leaders') returns categories, each with their own 'leaders' array
            leader_categories = team.get('leaders', [])
            
            for category in leader_categories:
                category_name = category.get('name')
                category_display = category.get('displayName')
                
                # The actual players are in category['leaders']
                category_leaders = category.get('leaders', [])
                
                for player_data in category_leaders:
                    athlete = player_data.get('athlete', {})
                    
                    if not athlete:
                        continue
                    
                    leader_info = {
                        'category': category_name,
                        'display_name': category_display,
                        'value': player_data.get('value'),
                        'display_value': player_data.get('displayValue'),
                        'athlete': athlete,
                        'team_name': team_name,
                        'team_abbrev': team_abbrev,
                        'home_away': home_away,
                        'position': athlete.get('position', {}).get('abbreviation'),
                        'jersey': athlete.get('jersey'),
                    }
                    team_data['leaders'].append(leader_info)
                    result['leaders'].append(leader_info)
            
            # Extract team statistics
            stats = team.get('statistics', [])
            team_data['statistics'] = [
                {'name': s.get('name'), 'value': s.get('value'), 'display': s.get('displayValue')}
                for s in stats
            ]
            
            if home_away == 'home':
                result['home_team'] = team_data
            else:
                result['away_team'] = team_data
                
        return result
    
    def _parse_all_games(self, sport: str, data: Dict) -> List[Dict[str, Any]]:
        """Parse all games from scoreboard."""
        games = []
        
        events = data.get('events', [])
        for event in events:
            game_data = self._parse_scoreboard_data(sport, {'events': [event]})
            games.append(game_data)
                
        return games
    
    async def _attach_scheduled_game_rosters(self, sport: str, games: List[Dict[str, Any]]) -> None:
        """Attach roster players for scheduled games that have no leaders yet."""
        if not games:
            return

        team_ids = []
        seen = set()
        for game in games:
            if not game.get('leaders'):
                for side in ('home_team', 'away_team'):
                    team_id = game.get(side, {}).get('id')
                    if team_id and team_id not in seen:
                        seen.add(team_id)
                        team_ids.append(team_id)

        if not team_ids:
            return

        logger.debug(f"ESPN roster fallback: fetching rosters for scheduled games: {len(team_ids)} teams")
        roster_cache = {}
        tasks = [self.get_team_roster(sport, team_id) for team_id in team_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for team_id, roster in zip(team_ids, results):
            if isinstance(roster, Exception) or not roster:
                continue
            roster_cache[team_id] = roster

        for game in games:
            if game.get('leaders'):
                continue
            for side in ('home_team', 'away_team'):
                team = game.get(side, {})
                team_id = team.get('id')
                home_away = team.get('home_away')
                team_abbrev = team.get('abbreviation')
                roster = roster_cache.get(team_id, [])
                for athlete in roster:
                    leader = {
                        'category': 'scheduled',
                        'display_name': 'Scheduled',
                        'value': None,
                        'display_value': '',
                        'athlete': athlete,
                        'team_name': team.get('name'),
                        'team_abbrev': team_abbrev,
                        'home_away': home_away,
                        'position': athlete.get('position'),
                        'jersey': athlete.get('jersey'),
                    }
                    game['leaders'].append(leader)

    def _parse_scheduled_games(self, sport: str, data: Dict) -> List[Dict[str, Any]]:
        """Parse scheduled games from scoreboard (no leaders since games haven't started)."""
        games = []
        
        events = data.get('events', [])
        for event in events:
            game_data = {
                'game': {
                    'id': event.get('id'),
                    'name': event.get('name'),
                    'status': event.get('status', {}).get('type', {}).get('name'),
                    'date': event.get('date'),
                },
                'home_team': {},
                'away_team': {},
                'leaders': [],  # No leaders for scheduled games
            }
            
            competitions = event.get('competitions', [])
            if competitions:
                comp = competitions[0]
                competitors = comp.get('competitors', [])
                
                for team in competitors:
                    team_info = team.get('team', {})
                    team_name = team_info.get('displayName')
                    team_abbrev = team_info.get('abbreviation')
                    home_away = team.get('homeAway')
                    
                    team_data = {
                        'id': team.get('id'),
                        'name': team_name,
                        'abbreviation': team_abbrev,
                        'home_away': home_away,
                    }
                    
                    if home_away == 'home':
                        game_data['home_team'] = team_data
                    else:
                        game_data['away_team'] = team_data
            
            games.append(game_data)
                
        return games
    
    async def get_player_season_stats(self, sport: str, player_id: str) -> Optional[Dict]:
        """Get player's season statistics."""
        cache_key = f"{sport}_{player_id}"
        if cache_key in self._player_cache:
            return self._player_cache[cache_key]
        return None
    
    async def build_player_profiles(self, sport: str, days_back: int = 7) -> Dict[str, Dict]:
        """Build player profiles by collecting stats from multiple days."""
        all_players = defaultdict(lambda: {
            'games': [],
            'stats': defaultdict(list),
        })
        return dict(all_players)
    
    async def get_team_leaders(self, sport: str, team_id: str) -> List[Dict]:
        """Get top performers for a team from recent games."""
        return []
    
    async def get_team_roster(self, sport: str, team_id: str) -> List[Dict[str, Any]]:
        """
        Get the roster for a specific team.
        Returns list of players with their IDs and basic info.
        """
        api_path = self.SPORT_API_PATHS.get(sport.lower())
        if not api_path:
            return []
            
        url = f"{self.base_url}/sports/{api_path}/teams/{team_id}/roster"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    logger.warning(f"Roster API returned {response.status_code} for team {team_id}")
                    return []
                    
                data = response.json()
                return self._parse_roster_data(data)
                
        except Exception as e:
            logger.error(f"Error fetching roster for team {team_id}: {e}")
            return []
    
    def _parse_roster_data(self, data: Dict) -> List[Dict[str, Any]]:
        """Parse roster data from ESPN API."""
        athletes = data.get('athletes', [])
        roster = []
        
        for athlete in athletes:
            # Handle position which might be a dict or a string
            position_data = athlete.get('position', {})
            if isinstance(position_data, dict):
                position_abbr = position_data.get('abbreviation')
                position_name = position_data.get('displayName')
            else:
                # If position is a string, use it as-is
                position_abbr = str(position_data) if position_data else None
                position_name = str(position_data) if position_data else None
            
            player_data = {
                'id': athlete.get('id'),
                'name': athlete.get('displayName') or athlete.get('fullName'),
                'position': position_abbr,
                'position_name': position_name,
                'jersey': athlete.get('jersey'),
                'active': athlete.get('active', True),
            }
            roster.append(player_data)
            
        return roster
    
    def generate_player_props_from_leaders(self, game_data: Dict, sport: str) -> List[Dict]:
        """Generate player props based on game leaders data."""
        props = []
        
        # Group leaders by player to get all their stats
        player_stats = defaultdict(dict)
        
        for leader in game_data.get('leaders', []):
            athlete = leader.get('athlete', {})
            player_id = athlete.get('id')
            player_name = athlete.get('fullName')
            team_name = leader.get('team_name')
            team_abbrev = leader.get('team_abbrev')
            position = leader.get('position')
            jersey = leader.get('jersey')
            
            if not player_id or not player_name:
                continue
            
            category = leader.get('category')
            value = leader.get('value', 0)
            
            # Store stats for this player
            if player_id not in player_stats:
                player_stats[player_id] = {
                    'player_id': player_id,
                    'player_name': player_name,
                    'team': team_name,
                    'team_abbrev': team_abbrev,
                    'position': position,
                    'jersey': jersey,
                    'categories': {}
                }
            
            player_stats[player_id]['categories'][category] = {
                'value': value,
                'display': leader.get('display_value')
            }
        
        # Generate props from collected player stats
        for player_id, data in player_stats.items():
            categories = data['categories']
            
            # Points props
            if 'points' in categories:
                pts = categories['points']['value']
                if pts and pts > 0:
                    line = int(pts * 0.75)  # Conservative estimate
                    props.append({
                        'player_id': data['player_id'],
                        'player_name': data['player_name'],
                        'team': data['team'],
                        'team_abbrev': data['team_abbrev'],
                        'position': data['position'],
                        'jersey': data['jersey'],
                        'category': 'points',
                        'line': max(10, line),
                        'recent_performance': pts,
                        'source': 'espn_leaders'
                    })
            
            # Rebounds props
            if 'rebounds' in categories:
                reb = categories['rebounds']['value']
                if reb and reb > 0:
                    line = int(reb * 0.7)
                    props.append({
                        'player_id': data['player_id'],
                        'player_name': data['player_name'],
                        'team': data['team'],
                        'team_abbrev': data['team_abbrev'],
                        'position': data['position'],
                        'jersey': data['jersey'],
                        'category': 'rebounds',
                        'line': max(4, line),
                        'recent_performance': reb,
                        'source': 'espn_leaders'
                    })
            
            # Assists props
            if 'assists' in categories:
                ast = categories['assists']['value']
                if ast and ast > 0:
                    line = int(ast * 0.7)
                    props.append({
                        'player_id': data['player_id'],
                        'player_name': data['player_name'],
                        'team': data['team'],
                        'team_abbrev': data['team_abbrev'],
                        'position': data['position'],
                        'jersey': data['jersey'],
                        'category': 'assists',
                        'line': max(3, line),
                        'recent_performance': ast,
                        'source': 'espn_leaders'
                    })
                
            # Three pointers made (NBA specific)
            if 'threePointersMade' in categories:
                three_pt = categories['threePointersMade']['value']
                if three_pt and three_pt > 0:
                    line = int(three_pt * 0.75)
                    props.append({
                        'player_id': data['player_id'],
                        'player_name': data['player_name'],
                        'team': data['team'],
                        'team_abbrev': data['team_abbrev'],
                        'position': data['position'],
                        'jersey': data['jersey'],
                        'category': 'three_pointers_made',
                        'line': max(2, line),
                        'recent_performance': three_pt,
                        'source': 'espn_leaders'
                    })
                
        return props


# Singleton instance
_player_stats_service = None

def get_player_stats_service() -> ESPNPlayerStatsService:
    """Get the singleton player stats service instance."""
    global _player_stats_service
    if _player_stats_service is None:
        _player_stats_service = ESPNPlayerStatsService()
    return _player_stats_service


# Quick test
async def test_player_stats():
    """Test the player stats service."""
    service = ESPNPlayerStatsService()
    
    print("=== Testing Today's NBA Games ===")
    games = await service.get_today_games_player_stats('nba')
    print(f"Found {len(games)} games with player stats")
    
    for game in games[:2]:  # Show first 2 games
        print(f"\nGame: {game.get('game', {}).get('name')}")
        print(f"Home: {game.get('home_team', {}).get('name')}")
        print(f"Away: {game.get('away_team', {}).get('name')}")
        
        # Show leaders
        print("\nTop Performers:")
        for leader in game.get('leaders', [])[:6]:
            athlete = leader.get('athlete', {})
            print(f"  - {athlete.get('fullName')} ({leader.get('team_abbrev')}): "
                  f"{leader.get('display_value')} {leader.get('category')}")
        
        # Generate props
        props = service.generate_player_props_from_leaders(game, 'nba')
        print(f"\nGenerated {len(props)} player props:")
        for prop in props[:6]:
            print(f"  - {prop['player_name']} ({prop['team_abbrev']}): "
                  f"{prop['category']} O/{prop['line']} (recent: {prop['recent_performance']})")


if __name__ == '__main__':
    asyncio.run(test_player_stats())
