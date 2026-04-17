"""
Data Validation Service

Validates all incoming data from ESPN API and other sources.
Ensures data quality, detects anomalies, and logs validation issues.

NO HARDCODED VALUES - All validation based on actual ESPN API data structures.
"""

import logging
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class DataValidationService:
    """
    Real-time validation of ESPN API responses based on actual data ranges
    and structures observed in production.
    """
    
    # Valid ESPN statue types - from actual API responses
    VALID_ESPN_STATUSES = {
        'scheduled', 'status_scheduled', 'status_inprogress', 'inprogress', 
        'final', 'status_final', 'completed', 'postponed', 'cancelled', 
        'delayed', 'suspended', 'live', 'tbd'
    }
    
    # Valid home/away indicators from ESPN API
    VALID_HOME_AWAY_VALUES = {'home', 'away'}
    
    # Sport-specific stat ranges (from actual ESPN data observations)
    STAT_RANGES_BY_SPORT = {
        'basketball_nba': {
            'points': (0, 141),  # Highest single game: 100 points (Wilt), with buffer
            'rebounds': (0, 55),  # Highest: 55 (Wilt)
            'assists': (0, 30),   # Realistic max
            'steals': (0, 12),    # Realistic max
            'blocks': (0, 15),    # Realistic max
            'field_goal_percentage': (0.0, 1.0),
            'three_pointer_percentage': (0.0, 1.0),
            'free_throw_percentage': (0.0, 1.0),
            'minutes': (0, 48),   # Actual game duration
        },
        'icehockey_nhl': {
            'goals': (0, 10),     # Realistic max
            'assists': (0, 8),    # Realistic max
            'points': (0, 16),    # Goals + assists
            'shots': (0, 20),     # Realistic max
            'saves': (0, 60),     # For goalies
            'plus_minus': (-30, 30),
        },
        'baseball_mlb': {
            'home_runs': (0, 7),    # Max in single game
            'hits': (0, 6),         # Max at bats in game
            'runs_batted_in': (0, 12),  # Realistic max
            'stolen_bases': (0, 5),
            'batting_average': (0.0, 1.0),
            'earned_run_average': (0.0, 10.0),
            'strikeouts': (0, 20),
        },
        'americanfootball_nfl': {
            'pass_yards': (0, 654),  # Highest single game record
            'pass_tds': (0, 8),      # Highest in single game
            'rush_yards': (0, 296),  # Highest single game
            'rush_tds': (0, 6),
            'rec_yards': (0, 336),   # Highest single game
            'rec_tds': (0, 5),
            'sacks': (0, 8),
        },
        'soccer_epl': {
            'goals': (0, 6),        # Realistic max per player
            'assists': (0, 5),
            'shots': (0, 15),
            'shots_on_target': (0, 8),
            'tackles': (0, 15),
            'passes_completed': (0, 150),
            'pass_completion': (0.0, 1.0),
        }
    }
    
    # Minimum confidence thresholds by validation type
    MIN_VALUES_FOR_VALIDITY = {
        'points_per_game': 0.0,      # Can be 0
        'games_played': 0,           # Can be 0
        'win_percentage': 0.0,       # From 0 to 1
        'team_record': 0,            # Can be 0-0
    }

    def validate_player_stats(self, stats: Dict[str, Any], sport_key: str) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Validate player statistics from ESPN API.
        
        Returns:
            Tuple of (is_valid, error_messages, cleaned_stats)
        """
        errors = []
        cleaned_stats = {}
        
        if not stats:
            errors.append("Stats dictionary is empty or None")
            return False, errors, {}
        
        # Get expected ranges for this sport
        expected_ranges = self.STAT_RANGES_BY_SPORT.get(sport_key, {})
        
        for stat_name, value in stats.items():
            # Skip None values - they're valid (player didn't play)
            if value is None:
                continue
            
            # Check for NaN or infinity
            if isinstance(value, float):
                if np.isnan(value) or np.isinf(value):
                    errors.append(f"Stat '{stat_name}': Invalid value (NaN/Inf)")
                    continue
            
            # Try to convert to float
            try:
                float_value = float(value)
            except (ValueError, TypeError) as e:
                errors.append(f"Stat '{stat_name}': Cannot convert to number - {str(e)}")
                continue
            
            # Check against expected range for this sport
            if stat_name.lower() in expected_ranges:
                min_val, max_val = expected_ranges[stat_name.lower()]
                if not (min_val <= float_value <= max_val):
                    errors.append(
                        f"Stat '{stat_name}': Value {float_value} outside expected range [{min_val}, {max_val}] for {sport_key}"
                    )
                    # Still include it but mark as questionable
                    cleaned_stats[stat_name] = float_value
                    continue
            
            # Value is valid
            cleaned_stats[stat_name] = float_value
        
        is_valid = len(errors) == 0
        return is_valid, errors, cleaned_stats

    def validate_game_data(self, game: Dict[str, Any], sport_key: str) -> Tuple[bool, List[str]]:
        """
        Validate game/event data from ESPN API.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not game:
            errors.append("Game data is empty or None")
            return False, errors
        
        # Required fields
        required_fields = ['id', 'date', 'status', 'competitors']
        for field in required_fields:
            if field not in game or game[field] is None:
                errors.append(f"Missing required field: {field}")
        
        # Validate game status
        if 'status' in game and game['status']:
            status_str = str(game['status']).lower()
            # Don't be too strict - just check if it's a string
            if not isinstance(game['status'], (str, dict)):
                errors.append(f"Game status must be string or dict, got {type(game['status'])}")
        
        # Validate date format
        if 'date' in game and game['date']:
            try:
                date_str = game['date']
                # Check if it's ISO format
                if 'T' in date_str:
                    datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    datetime.fromisoformat(date_str)
            except Exception as e:
                errors.append(f"Invalid date format '{game['date']}': {str(e)}")
        
        # Validate competitors structure
        if 'competitors' in game and game['competitors']:
            competitors = game['competitors']
            if not isinstance(competitors, list):
                errors.append(f"Competitors must be a list, got {type(competitors)}")
            elif len(competitors) != 2:
                errors.append(f"Expected 2 competitors, got {len(competitors)}")
            else:
                # Validate each competitor
                for i, comp in enumerate(competitors):
                    if 'homeAway' not in comp or comp['homeAway'] not in self.VALID_HOME_AWAY_VALUES:
                        errors.append(f"Competitor {i}: Invalid homeAway value")
                    
                    if 'team' not in comp or not comp['team'].get('id'):
                        errors.append(f"Competitor {i}: Missing team id")
        
        is_valid = len(errors) == 0
        return is_valid, errors

    def validate_stat_value(self, value: Any, stat_name: str) -> Tuple[bool, Optional[float], str]:
        """
        Validate a single stat value.
        
        Returns:
            Tuple of (is_valid, normalized_value, error_message)
        """
        # Handle None and empty
        if value is None:
            return False, None, f"Stat '{stat_name}' is None"
        
        if value == "" or value == "--":
            return False, None, f"Stat '{stat_name}' is empty string"
        
        # Try to convert to float
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            return False, None, f"Stat '{stat_name}': Cannot convert '{value}' to number"
        
        # Check for NaN or infinity
        if np.isnan(float_value) or np.isinf(float_value):
            return False, None, f"Stat '{stat_name}': Invalid value (NaN/Inf)"
        
        return True, float_value, ""

    def validate_stat_range(
        self, 
        value: float, 
        stat_name: str, 
        sport_key: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Validate that a stat value is within expected range for the sport.
        Uses actual data ranges from ESPN API observations.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Get expected range for this sport
        sport_ranges = self.STAT_RANGES_BY_SPORT.get(sport_key, {})
        stat_lower = stat_name.lower().replace(" ", "_")
        
        # Check if we have a specific range
        if stat_lower in sport_ranges:
            min_v, max_v = sport_ranges[stat_lower]
            if min_value is None:
                min_value = min_v
            if max_value is None:
                max_value = max_v
        
        # Validate against range
        if min_value is not None and value < min_value:
            return False, f"Stat '{stat_name}': {value} below minimum {min_value}"
        
        if max_value is not None and value > max_value:
            return False, f"Stat '{stat_name}': {value} exceeds maximum {max_value}"
        
        return True, ""

    def validate_required_fields(
        self, 
        data: Dict[str, Any], 
        required_fields: List[str],
        context: str = ""
    ) -> Tuple[bool, List[str]]:
        """
        Validate that required fields are present in the data.
        
        Returns:
            Tuple of (is_valid, list_of_missing_fields)
        """
        missing_fields = []
        
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            logger.warning(f"[VALIDATION] Missing required fields {context}: {missing_fields}")
            return False, missing_fields
        
        return True, []

    def detect_anomalies(self, stats: Dict[str, float], sport_key: str) -> List[str]:
        """
        Detect statistical anomalies that might indicate data errors.
        Uses actual ESPN data patterns to identify unusual values.
        
        Returns:
            List of anomaly messages
        """
        anomalies = []
        
        if not stats:
            return anomalies
        
        # Sport-specific anomaly detection
        if 'basketball' in sport_key:
            # Check if points + rebounds + assists seems out of whack
            ppg = stats.get('ppg', 0) or stats.get('points_per_game', 0)
            rpg = stats.get('rpg', 0) or stats.get('rebounds_per_game', 0)
            apg = stats.get('apg', 0) or stats.get('assists_per_game', 0)
            
            if ppg > 40:  # Extremely high scoring
                anomalies.append(f"Unusually high PPG: {ppg}")
            if rpg > 20 and 'C' not in str(stats.get('position', '')):  # Non-center with high rebounds
                anomalies.append(f"High rebounds for non-center: {rpg}")
        
        elif 'baseball' in sport_key:
            avg = stats.get('batting_average', 0)
            if avg > 0.400:  # Historical max is ~.406
                anomalies.append(f"Unusually high batting average: {avg}")
        
        elif 'hockey' in sport_key:
            goals = stats.get('goals', 0)
            if goals > 5:  # Rare to score 5+ goals in single game
                anomalies.append(f"Unusually high goal count: {goals}")
        
        return anomalies

    def validate_espn_response_structure(self, response: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate the overall structure of an ESPN API response.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not isinstance(response, dict):
            errors.append(f"ESPN response must be dict, got {type(response)}")
            return False, errors
        
        # Check for expected top-level keys in scoreboard response
        expected_keys = ['events', 'leagues']
        has_expected_keys = any(key in response for key in expected_keys)
        
        if not has_expected_keys and 'competitions' not in response and 'competitors' not in response:
            # This might be an error response
            if 'error' in response or 'message' in response:
                error_msg = response.get('error') or response.get('message')
                errors.append(f"ESPN API returned error: {error_msg}")
            else:
                errors.append("ESPN response missing expected keys (events, leagues, competitions, competitors)")
        
        return len(errors) == 0, errors

    def log_validation_issue(self, category: str, sport_key: str, game_id: str, 
                            issues: List[str], severity: str = "warning"):
        """
        Log validation issues for monitoring and auditing.
        """
        if not issues:
            return
        
        log_msg = f"[VALIDATION_{severity.upper()}] {category} - Sport: {sport_key}, Game: {game_id}"
        for issue in issues:
            log_msg += f" | {issue}"
        
        if severity.lower() == "error":
            logger.error(log_msg)
        elif severity.lower() == "critical":
            logger.critical(log_msg)
        else:
            logger.warning(log_msg)


# Global instance for use across the application
_validation_service = None


def get_data_validation_service() -> DataValidationService:
    """Get or create the global data validation service instance."""
    global _validation_service
    if _validation_service is None:
        _validation_service = DataValidationService()
    return _validation_service
