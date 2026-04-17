import pytest
import numpy as np
import pandas as pd
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.weather_service import WeatherService
from app.services.injury_service import InjuryImpactService

@pytest.fixture
def weather_service():
    return WeatherService(api_key="test_weather_key")

@pytest.fixture
def injury_service():
    return InjuryImpactService()

@pytest.fixture
def mock_weather_response():
    return {
        "main": {
            "temp": 72.5,
            "humidity": 65,
            "pressure": 1013,
            "wind_speed": 8.2
        },
        "wind": {
            "speed": 8.2,
            "deg": 245
        },
        "weather": [
            {
                "main": "Clear",
                "description": "clear sky"
            }
        ],
        "visibility": 10000,
        "dt": 1640995200
    }

@pytest.fixture
def mock_injury_data():
    return [
        {
            "player_name": "LeBron James",
            "team": "Lakers",
            "injury_type": "ankle_sprain",
            "severity": "moderate",
            "expected_return": "2024-02-15",
            "position": "SF",
            "impact_rating": 8.5
        },
        {
            "player_name": "Anthony Davis",
            "team": "Lakers",
            "injury_type": "back_spasms",
            "severity": "mild",
            "expected_return": "2024-02-10",
            "position": "PF",
            "impact_rating": 7.2
        }
    ]

@pytest.mark.asyncio
async def test_get_weather_for_game(weather_service, mock_weather_response):
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_weather_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await weather_service.get_weather_for_game(
            venue_city="Los Angeles",
            venue_state="CA",
            game_date="2024-01-15T20:00:00Z"
        )
        
        assert result is not None
        assert 'temperature' in result
        assert 'humidity' in result
        assert 'wind_speed' in result
        assert 'weather_impact_score' in result
        assert 'precipitation_probability' in result
        assert 0 <= result['weather_impact_score'] <= 10

def test_calculate_weather_impact_score(weather_service):
    # Test different weather conditions
    
    # Ideal conditions
    ideal_weather = {
        'temperature': 70,
        'humidity': 50,
        'wind_speed': 5,
        'precipitation': 0
    }
    ideal_score = weather_service._calculate_weather_impact_score(ideal_weather)
    assert 0 <= ideal_score <= 2
    
    # Poor conditions
    poor_weather = {
        'temperature': 95,
        'humidity': 90,
        'wind_speed': 25,
        'precipitation': 0.5
    }
    poor_score = weather_service._calculate_weather_impact_score(poor_weather)
    assert 7 <= poor_score <= 10

def test_calculate_precipitation_probability(weather_service):
    # Test precipitation probability calculation
    weather_data = {
        'humidity': 85,
        'cloud_cover': 80,
        'pressure': 1000
    }
    
    probability = weather_service._calculate_precipitation_probability(weather_data)
    
    assert 0 <= probability <= 1
    assert isinstance(probability, float)

def test_get_weather_forecast(weather_service, mock_weather_response):
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_weather_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = weather_service._get_weather_forecast(34.0522, -118.2437, "2024-01-15")
        
        assert result is not None
        assert 'temperature' in result
        assert 'humidity' in result
        assert 'wind_speed' in result

@pytest.mark.asyncio
async def test_get_injury_impact_for_team(injury_service, mock_injury_data):
    with patch.object(injury_service, 'fetch_team_injuries') as mock_fetch:
        mock_fetch.return_value = mock_injury_data
        
        result = await injury_service.get_injury_impact_for_team("Lakers")
        
        assert result is not None
        assert 'total_impact_score' in result
        assert 'key_injuries' in result
        assert 'position_impacts' in result
        assert 'return_timeline' in result
        assert 0 <= result['total_impact_score'] <= 10
        assert len(result['key_injuries']) == 2

def test_calculate_injury_impact_score(injury_service):
    # Test injury impact calculation
    injuries = [
        {"severity": "severe", "impact_rating": 9.0, "position": "PG"},
        {"severity": "mild", "impact_rating": 3.0, "position": "SG"},
        {"severity": "moderate", "impact_rating": 6.5, "position": "C"}
    ]
    
    impact_score = injury_service._calculate_injury_impact_score(injuries)
    
    assert 0 <= impact_score <= 10
    assert isinstance(impact_score, float)

def test_calculate_position_impact(injury_service):
    # Test position-specific impact calculation
    injuries = [
        {"severity": "severe", "impact_rating": 9.0, "position": "PG"},
        {"severity": "moderate", "impact_rating": 6.5, "position": "C"}
    ]
    
    position_impacts = injury_service._calculate_position_impact(injuries)
    
    assert 'PG' in position_impacts
    assert 'C' in position_impacts
    assert 0 <= position_impacts['PG'] <= 10
    assert 0 <= position_impacts['C'] <= 10

def test_calculate_return_timeline(injury_service):
    # Test return timeline calculation
    injuries = [
        {"expected_return": "2024-02-15", "severity": "moderate"},
        {"expected_return": "2024-02-10", "severity": "mild"},
        {"expected_return": "2024-03-01", "severity": "severe"}
    ]
    
    timeline = injury_service._calculate_return_timeline(injuries)
    
    assert 'short_term' in timeline
    assert 'medium_term' in timeline
    assert 'long_term' in timeline
    assert isinstance(timeline['short_term'], int)

def test_adjust_player_impact_for_severity(injury_service):
    # Test severity adjustment
    base_impact = 8.0
    
    severe_impact = injury_service._adjust_player_impact_for_severity(base_impact, "severe")
    mild_impact = injury_service._adjust_player_impact_for_severity(base_impact, "mild")
    moderate_impact = injury_service._adjust_player_impact_for_severity(base_impact, "moderate")
    
    assert severe_impact > moderate_impact > mild_impact
    assert 0 <= severe_impact <= 10
    assert 0 <= mild_impact <= 10
    assert 0 <= moderate_impact <= 10

def test_get_injury_impact_for_game(injury_service, mock_injury_data):
    with patch.object(injury_service, 'fetch_team_injuries') as mock_fetch:
        mock_fetch.side_effect = lambda team: [
            injury for injury in mock_injury_data if injury['team'] == team
        ]
        
        result = injury_service.get_injury_impact_for_game("Lakers", "Celtics")
        
        assert result is not None
        assert 'home_impact' in result
        assert 'away_impact' in result
        assert 'combined_impact' in result
        assert 0 <= result['combined_impact'] <= 10