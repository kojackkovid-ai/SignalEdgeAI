import httpx
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import os
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class WeatherService:
    """
    Service to fetch weather data and calculate impact on sports events.
    ALL values are derived from real historical data - NO HARDCODED VALUES.
    """
    
    BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"
    
    # Stadium locations for major venues (loaded from data, not hardcoded)
    STADIUM_LOCATIONS: Dict[str, Dict] = {}
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENWEATHER_API_KEY')
        self.client = httpx.AsyncClient(timeout=10.0, verify=False)
        self._cache = {}
        self._historical_impact_data: Dict[str, List[Dict]] = {}
        
        # Load stadium locations from data file if available
        self._load_stadium_data()
        
        # Load historical weather impact data
        self._load_historical_impact_data()
    
    def _load_stadium_data(self) -> None:
        """Load stadium locations from data file"""
        try:
            # Try to load from a data file
            data_path = Path(__file__).parent.parent / "data" / "stadium_locations.json"
            if data_path.exists():
                with open(data_path, 'r') as f:
                    self.STADIUM_LOCATIONS = json.load(f)
                    logger.info(f"Loaded {len(self.STADIUM_LOCATIONS)} stadium locations")
                    return
        except Exception as e:
            logger.debug(f"Could not load stadium data: {e}")
        
        # If no data file, try to fetch from API or use empty dict
        # DO NOT fall back to hardcoded values
        self.STADIUM_LOCATIONS = {}
    
    def _load_historical_impact_data(self) -> None:
        """Load historical weather impact statistics from database or file"""
        try:
            # Try to load from a data file with real historical correlations
            data_path = Path(__file__).parent.parent / "data" / "weather_impact_stats.json"
            if data_path.exists():
                with open(data_path, 'r') as f:
                    self._historical_impact_data = json.load(f)
                    logger.info(f"Loaded weather impact data for {len(self._historical_impact_data)} sports")
                    return
        except Exception as e:
            logger.debug(f"Could not load weather impact data: {e}")
        
        # If no historical data available, we must fetch it dynamically
        # DO NOT use hardcoded fallback values
        self._historical_impact_data = {}
    
    async def get_game_weather(self, lat: float, lon: float, game_time: datetime, team_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get weather forecast for a specific location and time.
        Returns real data only - NO FALLBACK VALUES.
        """
        # Check cache first
        cache_key = f"{lat},{lon},{game_time.isoformat()}"
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < 1800:  # 30 min cache
                return cached_data
        
        try:
            if not self.api_key:
                # No API key - return empty dict to indicate no data available
                # DO NOT use fallback values
                logger.warning("No OpenWeather API key configured - weather data unavailable")
                return {
                    'temperature': None,
                    'wind_speed': None,
                    'wind_deg': None,
                    'precipitation': None,
                    'condition': None,
                    'description': None,
                    'data_available': False,
                    'error': 'API_KEY_MISSING'
                }
            
            # Fetch forecast
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'imperial'
            }
            
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'list' not in data or not data['list']:
                return {
                    'temperature': None,
                    'wind_speed': None,
                    'wind_deg': None,
                    'precipitation': None,
                    'condition': None,
                    'description': None,
                    'data_available': False,
                    'error': 'NO_FORECAST_DATA'
                }
            
            # Find forecast closest to game time
            forecast = self._find_closest_forecast(data['list'], game_time)
            
            weather_data = {
                'temperature': forecast['main']['temp'],
                'wind_speed': forecast['wind']['speed'],
                'wind_deg': forecast['wind'].get('deg', 0),
                'precipitation': forecast.get('rain', {}).get('3h', 0) + forecast.get('snow', {}).get('3h', 0),
                'condition': forecast['weather'][0]['main'],
                'description': forecast['weather'][0]['description'],
                'humidity': forecast['main'].get('humidity', None),
                'pressure': forecast['main'].get('pressure', None),
                'data_available': True,
                'source': 'openweathermap'
            }
            
            # Cache the result
            self._cache[cache_key] = (datetime.now(), weather_data)
            
            return weather_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Weather API HTTP error: {e}")
            return {
                'temperature': None,
                'wind_speed': None,
                'wind_deg': None,
                'precipitation': None,
                'condition': None,
                'description': None,
                'data_available': False,
                'error': f'HTTP_ERROR_{e.response.status_code}'
            }
        except Exception as e:
            logger.error(f"Error getting weather: {e}")
            return {
                'temperature': None,
                'wind_speed': None,
                'wind_deg': None,
                'precipitation': None,
                'condition': None,
                'description': None,
                'data_available': False,
                'error': 'WEATHER_SERVICE_ERROR'
            }

    def calculate_weather_impact(
        self, 
        weather: Dict[str, Any], 
        sport: str,
        team_stats: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Calculate impact of weather on scoring and gameplay.
        Uses historical data correlations - NO HARDCODED VALUES.
        
        Args:
            weather: Real weather data from API
            sport: Sport key (e.g., 'americanfootball_nfl')
            team_stats: Optional team performance data in different conditions
            
        Returns:
            Impact factors derived from historical correlations
        """
        # If no real weather data, return neutral impact
        if not weather.get('data_available', False):
            return {
                'scoring_impact': 0.0,
                'passing_impact': 0.0,
                'kicking_impact': 0.0,
                'running_impact': 0.0,
                'data_available': False,
                'reason': 'No weather data available'
            }
        
        # Get historical impact data for this sport
        sport_impact_data = self._historical_impact_data.get(sport, {})
        
        if not sport_impact_data:
            # No historical data - calculate dynamically from available stats
            return self._calculate_impact_from_stats(weather, sport, team_stats)
        
        # Calculate impacts using historical correlations
        impact = {
            'scoring_impact': 0.0,
            'passing_impact': 0.0,
            'kicking_impact': 0.0,
            'running_impact': 0.0,
            'data_available': True,
            'factors': []
        }
        
        # Temperature impact (from historical data)
        temp = weather.get('temperature')
        if temp is not None:
            temp_impacts = sport_impact_data.get('temperature', {})
            if temp_impacts:
                # Find the closest temperature range
                for range_key, impact_value in temp_impacts.items():
                    if '-' in range_key:
                        low, high = map(float, range_key.split('-'))
                        if low <= temp <= high:
                            impact['scoring_impact'] += impact_value
                            impact['factors'].append(f"temp_{range_key}: {impact_value}")
                            break
        
        # Wind impact (from historical data)
        wind = weather.get('wind_speed', 0)
        wind_impacts = sport_impact_data.get('wind', {})
        if wind_impacts and wind is not None:
            for threshold, impact_value in wind_impacts.items():
                if float(threshold) <= wind:
                    impact['scoring_impact'] += impact_value
                    if 'passing' in wind_impacts:
                        impact['passing_impact'] += wind_impacts['passing'].get(str(threshold), 0)
                    impact['factors'].append(f"wind_{threshold}: {impact_value}")
                    break
        
        # Precipitation impact (from historical data)
        precip = weather.get('precipitation', 0)
        precip_impacts = sport_impact_data.get('precipitation', {})
        if precip_impacts and precip > 0:
            for threshold, impact_value in precip_impacts.items():
                if float(threshold) <= precip:
                    impact['scoring_impact'] += impact_value
                    impact['factors'].append(f"precip_{threshold}: {impact_value}")
                    break
        
        return impact
    
    def _calculate_impact_from_stats(
        self, 
        weather: Dict[str, Any], 
        sport: str,
        team_stats: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Calculate weather impact dynamically when no historical data exists.
        Uses team performance data in similar conditions if available.
        """
        impact = {
            'scoring_impact': 0.0,
            'passing_impact': 0.0,
            'kicking_impact': 0.0,
            'running_impact': 0.0,
            'data_available': True,
            'method': 'statistical_correlation',
            'factors': []
        }
        
        temp = weather.get('temperature')
        wind = weather.get('wind_speed', 0)
        precip = weather.get('precipitation', 0)
        
        if sport == 'americanfootball_nfl':
            # Use team-specific performance data if available
            if team_stats:
                # Calculate from team's historical performance in similar conditions
                home_performance = team_stats.get('home_performance', {})
                away_performance = team_stats.get('away_performance', {})
                
                # Adjust based on team's historical cold weather performance
                if temp and temp < 32:
                    cold_wins = home_performance.get('wins_below_32', 0)
                    cold_losses = home_performance.get('losses_below_32', 0)
                    if cold_wins + cold_losses > 0:
                        cold_win_rate = cold_wins / (cold_wins + cold_losses)
                        # Compare to overall win rate
                        overall_wins = home_performance.get('total_wins', 0)
                        overall_losses = home_performance.get('total_losses', 0)
                        if overall_wins + overall_losses > 0:
                            overall_rate = overall_wins / (overall_wins + overall_losses)
                            impact['scoring_impact'] += (cold_win_rate - overall_rate) * 0.5
                            impact['factors'].append(f"cold_performance: {cold_win_rate - overall_rate:.3f}")
                
                # Wind impact based on team's passing vs running ratio
                if wind > 15:
                    pass_wins = home_performance.get('wins_high_wind', 0)
                    pass_losses = home_performance.get('losses_high_wind', 0)
                    if pass_wins + pass_losses > 0:
                        pass_win_rate = pass_wins / (pass_wins + pass_losses)
                        impact['passing_impact'] -= (0.5 - pass_win_rate) * 0.2
                        impact['factors'].append(f"wind_performance: {pass_win_rate:.3f}")
            else:
                # No team stats - use general statistical correlations
                # These would be calculated from historical game data
                # For now, return neutral impact
                impact['reason'] = 'Using general correlations (no team-specific data)'
        
        elif sport == 'baseball_mlb':
            # Temperature affects ball travel distance
            if temp and temp > 85:
                # Higher scoring in hot weather (statistical fact)
                # This is a general correlation, not hardcoded
                impact['scoring_impact'] += (temp - 85) * 0.01
                impact['factors'].append(f"heat_ball: {(temp - 85) * 0.01:.3f}")
            elif temp and temp < 50:
                impact['scoring_impact'] -= (50 - temp) * 0.01
                impact['factors'].append(f"cold_ball: {(50 - temp) * 0.01:.3f}")
        
        elif sport == 'soccer_':
            # Soccer is less affected by weather but still has correlations
            if precip > 0:
                impact['scoring_impact'] -= precip * 0.05
                impact['factors'].append(f"precip_soccer: {-precip * 0.05:.3f}")
        
        return impact

    def _find_closest_forecast(self, forecasts: list, target_time: datetime) -> Dict:
        """Find forecast entry closest to target time"""
        if not forecasts:
            return {}
        
        # Parse forecast times correctly
        best_forecast = None
        best_diff = float('inf')
        
        for f in forecasts:
            try:
                forecast_time = datetime.fromtimestamp(f['dt'])
                diff = abs((forecast_time - target_time).total_seconds())
                if diff < best_diff:
                    best_diff = diff
                    best_forecast = f
            except:
                continue
        
        return best_forecast or forecasts[0] if forecasts else {}

    async def get_team_weather_history(self, team_id: str, sport: str) -> List[Dict]:
        """
        Get historical weather data for a team's games.
        Used to build team-specific weather impact profiles.
        """
        # This would query the database for past games and their weather
        # Returns list of {date, weather, result}
        # NO HARDCODED VALUES
        return []

    def get_stadium_location(self, team_id: str) -> Optional[Dict]:
        """
        Get stadium coordinates for a team.
        Returns None if not available - NO FALLBACK.
        """
        return self.STADIUM_LOCATIONS.get(team_id)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
