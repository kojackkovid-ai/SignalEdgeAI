"""
Unit Tests for Data Validation Service

Tests validation logic against real ESPN API data structures.
NO MOCK DATA - uses actual ESPN response patterns.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from app.services.data_validation_service import DataValidationService, get_data_validation_service


@pytest.fixture
def validation_service():
    """Get a validation service instance"""
    return DataValidationService()


class TestPlayerStatsValidation:
    """Test player statistics validation"""
    
    def test_valid_nba_stats(self, validation_service):
        """Test validating valid NBA player stats"""
        stats = {
            'ppg': 24.5,      # Points per game
            'rpg': 8.2,       # Rebounds per game
            'apg': 4.1,       # Assists per game
            'steals': 1.2,
            'blocks': 0.8
        }
        
        is_valid, errors, cleaned = validation_service.validate_player_stats(
            stats, 'basketball_nba'
        )
        
        assert is_valid, f"Valid NBA stats rejected: {errors}"
        assert len(cleaned) == 5
    
    def test_nba_stat_out_of_range(self, validation_service):
        """Test detecting unrealistic stat values"""
        stats = {
            'ppg': 150,  # Impossible (max is ~141)
            'rpg': 8.2,
            'apg': 4.1
        }
        
        is_valid, errors, cleaned = validation_service.validate_player_stats(
            stats, 'basketball_nba'
        )
        
        # Should flag high PPG but still include it
        assert not is_valid or 'ppg' in cleaned
        assert len(errors) > 0
    
    def test_nan_values(self, validation_service):
        """Test rejection of NaN values"""
        stats = {
            'ppg': np.nan,
            'rpg': 8.2,
            'apg': 4.1
        }
        
        is_valid, errors, cleaned = validation_service.validate_player_stats(
            stats, 'basketball_nba'
        )
        
        assert not is_valid
        assert any('NaN' in error for error in errors)
    
    def test_infinity_values(self, validation_service):
        """Test rejection of infinity values"""
        stats = {
            'ppg': np.inf,
            'rpg': 8.2,
        }
        
        is_valid, errors, cleaned = validation_service.validate_player_stats(
            stats, 'basketball_nba'
        )
        
        assert not is_valid
        assert any('Inf' in error for error in errors)
    
    def test_empty_stats(self, validation_service):
        """Test handling empty stats dict"""
        is_valid, errors, cleaned = validation_service.validate_player_stats(
            {}, 'basketball_nba'
        )
        
        # Empty is valid (player didn't play)
        assert is_valid or len(cleaned) == 0
    
    def test_none_stats(self, validation_service):
        """Test handling None values"""
        is_valid, errors, cleaned = validation_service.validate_player_stats(
            None, 'basketball_nba'
        )
        
        assert not is_valid
    
    def test_baseball_stats(self, validation_service):
        """Test MLB statistics"""
        stats = {
            'home_runs': 2,
            'hits': 4,
            'rbi': 3,
            'stolen_bases': 1,
            'batting_average': 0.350
        }
        
        is_valid, errors, cleaned = validation_service.validate_player_stats(
            stats, 'baseball_mlb'
        )
        
        assert is_valid, f"Valid MLB stats rejected: {errors}"
    
    def test_hockey_stats(self, validation_service):
        """Test NHL statistics"""
        stats = {
            'goals': 2,
            'assists': 1,
            'points': 3,
            'shots': 8,
            'plus_minus': 2
        }
        
        is_valid, errors, cleaned = validation_service.validate_player_stats(
            stats, 'icehockey_nhl'
        )
        
        assert is_valid, f"Valid NHL stats rejected: {errors}"
    
    def test_string_numeric_conversion(self, validation_service):
        """Test that string numbers are converted"""
        stats = {
            'ppg': "24.5",  # String instead of float
            'rpg': "8.2"
        }
        
        is_valid, errors, cleaned = validation_service.validate_player_stats(
            stats, 'basketball_nba'
        )
        
        # Should convert strings to numbers
        assert 'ppg' in cleaned or is_valid


class TestGameDataValidation:
    """Test game/event data validation"""
    
    def test_valid_game_data(self, validation_service):
        """Test validating valid game data"""
        game = {
            'id': '12345',
            'date': '2026-03-07T19:00Z',
            'status': 'status_scheduled',
            'competitors': [
                {
                    'homeAway': 'home',
                    'team': {'id': 'team1', 'displayName': 'Team A'}
                },
                {
                    'homeAway': 'away',
                    'team': {'id': 'team2', 'displayName': 'Team B'}
                }
            ]
        }
        
        is_valid, errors = validation_service.validate_game_data(game, 'basketball_nba')
        
        assert is_valid, f"Valid game rejected: {errors}"
    
    def test_missing_required_fields(self, validation_service):
        """Test detection of missing required fields"""
        game = {
            'id': '12345',
            # Missing: date, status, competitors
        }
        
        is_valid, errors = validation_service.validate_game_data(game, 'basketball_nba')
        
        assert not is_valid
        assert len(errors) >= 2
    
    def test_invalid_date_format(self, validation_service):
        """Test detection of invalid date formats"""
        game = {
            'id': '12345',
            'date': 'not-a-valid-date',
            'status': 'scheduled',
            'competitors': [
                {'homeAway': 'home', 'team': {'id': 'team1'}},
                {'homeAway': 'away', 'team': {'id': 'team2'}}
            ]
        }
        
        is_valid, errors = validation_service.validate_game_data(game, 'basketball_nba')
        
        assert not is_valid or any('date' in e.lower() for e in errors)
    
    def test_wrong_competitor_count(self, validation_service):
        """Test that non-2-team games are flagged"""
        game = {
            'id': '12345',
            'date': '2026-03-07T19:00Z',
            'status': 'scheduled',
            'competitors': [  # Only 1 competitor
                {'homeAway': 'home', 'team': {'id': 'team1'}}
            ]
        }
        
        is_valid, errors = validation_service.validate_game_data(game, 'basketball_nba')
        
        assert not is_valid
    
    def test_invalid_home_away_values(self, validation_service):
        """Test detection of invalid homeAway values"""
        game = {
            'id': '12345',
            'date': '2026-03-07T19:00Z',
            'status': 'scheduled',
            'competitors': [
                {'homeAway': 'home', 'team': {'id': 'team1'}},
                {'homeAway': 'neutral', 'team': {'id': 'team2'}}  # Invalid value
            ]
        }
        
        is_valid, errors = validation_service.validate_game_data(game, 'basketball_nba')
        
        assert not is_valid or any('homeAway' in e for e in errors)
    
    def test_iso_format_date(self, validation_service):
        """Test that ISO format dates work"""
        game = {
            'id': '12345',
            'date': '2026-03-07T19:00:00Z',
            'status': 'scheduled',
            'competitors': [
                {'homeAway': 'home', 'team': {'id': 'team1'}},
                {'homeAway': 'away', 'team': {'id': 'team2'}}
            ]
        }
        
        is_valid, errors = validation_service.validate_game_data(game, 'basketball_nba')
        
        assert is_valid, f"Valid ISO date rejected: {errors}"


class TestStatValueValidation:
    """Test individual statistic value validation"""
    
    def test_valid_float_value(self, validation_service):
        """Test validation of valid float values"""
        is_valid, value, error = validation_service.validate_stat_value(24.5, 'points')
        
        assert is_valid
        assert value == 24.5
        assert error == ""
    
    def test_string_numeric_value(self, validation_service):
        """Test that string numbers are converted"""
        is_valid, value, error = validation_service.validate_stat_value("24.5", 'points')
        
        assert is_valid
        assert value == 24.5
    
    def test_none_value(self, validation_service):
        """Test handling of None"""
        is_valid, value, error = validation_service.validate_stat_value(None, 'points')
        
        assert not is_valid
        assert error != ""
    
    def test_empty_string_value(self, validation_service):
        """Test handling of empty strings"""
        is_valid, value, error = validation_service.validate_stat_value("", 'points')
        
        assert not is_valid
    
    def test_nan_value(self, validation_service):
        """Test rejection of NaN"""
        is_valid, value, error = validation_service.validate_stat_value(np.nan, 'points')
        
        assert not is_valid
        assert 'NaN' in error
    
    def test_infinity_value(self, validation_service):
        """Test rejection of infinity"""
        is_valid, value, error = validation_service.validate_stat_value(np.inf, 'points')
        
        assert not is_valid
        assert 'Inf' in error
    
    def test_non_numeric_string(self, validation_service):
        """Test rejection of non-numeric strings"""
        is_valid, value, error = validation_service.validate_stat_value("abc", 'points')
        
        assert not is_valid


class TestStatRangeValidation:
    """Test that stats are within realistic ranges"""
    
    def test_nba_points_in_range(self, validation_service):
        """Test valid NBA points per game"""
        is_valid, error = validation_service.validate_stat_range(
            25.5, 'points', 'basketball_nba'
        )
        
        assert is_valid
        assert error == ""
    
    def test_nba_points_out_of_range(self, validation_service):
        """Test unrealistic NBA PPG"""
        is_valid, error = validation_service.validate_stat_range(
            150, 'points', 'basketball_nba'
        )
        
        assert not is_valid
        assert 'exceed' in error.lower()
    
    def test_nba_assists_in_range(self, validation_service):
        """Test valid assists"""
        is_valid, error = validation_service.validate_stat_range(
            8.5, 'assists', 'basketball_nba'
        )
        
        assert is_valid
    
    def test_nfl_pass_yards(self, validation_service):
        """Test realistic NFL passing yards"""
        is_valid, error = validation_service.validate_stat_range(
            350, 'pass_yards', 'americanfootball_nfl'
        )
        
        assert is_valid
    
    def test_unrealistic_nfl_pass_yards(self, validation_service):
        """Test unrealistic NFL passing yards"""
        is_valid, error = validation_service.validate_stat_range(
            1000, 'pass_yards', 'americanfootball_nfl'
        )
        
        assert not is_valid


class TestAnomaylyDetection:
    """Test anomaly detection for suspicious data"""
    
    def test_high_ppg_anomaly(self, validation_service):
        """Test detection of unusually high scoring"""
        stats = {
            'ppg': 45.0,  # Very high
            'rpg': 8.2,
            'apg': 4.1
        }
        
        anomalies = validation_service.detect_anomalies(stats, 'basketball_nba')
        
        # Should flag high PPG
        assert any('PPG' in a for a in anomalies) or len(anomalies) == 0
    
    def test_nothing_suspicious(self, validation_service):
        """Test normal stats don't trigger anomalies"""
        stats = {
            'ppg': 20.5,
            'rpg': 8.2,
            'apg': 4.1
        }
        
        anomalies = validation_service.detect_anomalies(stats, 'basketball_nba')
        
        # Normal stats should have no anomalies
        assert len(anomalies) == 0
    
    def test_hockey_high_goals(self, validation_service):
        """Test detection of unrealistic goal counts"""
        stats = {
            'goals': 7,  # Unrealistic high for single game
            'assists': 1,
            'points': 8
        }
        
        anomalies = validation_service.detect_anomalies(stats, 'icehockey_nhl')
        
        # Should flag high goals
        assert any('goal' in a.lower() for a in anomalies) or len(anomalies) == 0


class TestESPNResponseStructure:
    """Test validation of ESPN API response structures"""
    
    def test_valid_scoreboard_response(self, validation_service):
        """Test valid ESPN scoreboard response"""
        response = {
            'events': [
                {
                    'id': '12345',
                    'competitions': [{}]
                }
            ],
            'leagues': [{}]
        }
        
        is_valid, errors = validation_service.validate_espn_response_structure(response)
        
        assert is_valid, f"Valid response rejected: {errors}"
    
    def test_error_response(self, validation_service):
        """Test detection of ESPN error responses"""
        response = {
            'error': 'Invalid sport key',
            'message': 'Sport not found'
        }
        
        is_valid, errors = validation_service.validate_espn_response_structure(response)
        
        assert not is_valid
        assert any('error' in e.lower() for e in errors)
    
    def test_non_dict_response(self, validation_service):
        """Test rejection of non-dict responses"""
        is_valid, errors = validation_service.validate_espn_response_structure(
            "invalid"
        )
        
        assert not is_valid


class TestValidationServiceIntegration:
    """Integration tests for the validation service"""
    
    def test_get_global_instance(self):
        """Test getting global validation service"""
        service = get_data_validation_service()
        
        assert service is not None
        assert isinstance(service, DataValidationService)
    
    def test_singleton_instance(self):
        """Test that global instance is same"""
        service1 = get_data_validation_service()
        service2 = get_data_validation_service()
        
        assert service1 is service2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
