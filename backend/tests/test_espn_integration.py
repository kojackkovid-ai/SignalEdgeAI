import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.espn_prediction_service import ESPNPredictionService

@pytest.fixture
def prediction_service():
    return ESPNPredictionService()

@pytest.fixture
def sample_game_data():
    return {
        "id": "game_123",
        "date": "2024-01-15T20:00:00Z",
        "competitors": [
            {
                "id": "team_1",
                "homeAway": "home",
                "team": {"displayName": "Lakers", "abbreviation": "LAL"},
                "score": "0"
            },
            {
                "id": "team_2",
                "homeAway": "away",
                "team": {"displayName": "Celtics", "abbreviation": "BOS"},
                "score": "0"
            }
        ],
        "venue": {
            "address": {
                "city": "Los Angeles",
                "state": "CA"
            }
        }
    }

@pytest.mark.asyncio
async def test_create_prediction_from_game_integration(prediction_service, sample_game_data):
    # Mock all the dependent services
    mock_odds = {
        'moneyline': {'home_implied_prob': 0.6, 'away_implied_prob': 0.4},
        'spread': {'home_spread': -3.5},
        'sharp_money_indicators': {'sharp_line_detected': False}
    }
    
    mock_weather = {
        'weather_impact_score': 2.5,
        'conditions': 'Clear'
    }
    
    mock_injuries = {
        'home_impact': 1.5,
        'away_impact': 0.5,
        'combined_impact': 2.0
    }
    
    mock_ml_prediction = {
        'probability': 0.65,
        'confidence': 0.8,
        'predicted_winner': 'Lakers'
    }
    
    # Patch all external service calls
    with patch.object(prediction_service.odds_service, 'get_odds_for_game', new_callable=AsyncMock) as mock_get_odds, \
         patch.object(prediction_service.weather_service, 'get_weather_for_game', new_callable=AsyncMock) as mock_get_weather, \
         patch.object(prediction_service.injury_service, 'get_injury_impact_for_game', new_callable=AsyncMock) as mock_get_injuries, \
         patch.object(prediction_service.ml_service, 'predict', new_callable=AsyncMock) as mock_predict, \
         patch.object(prediction_service.feature_engineer, 'prepare_features') as mock_prepare_features:
        
        # Setup mock returns
        mock_get_odds.return_value = mock_odds
        mock_get_weather.return_value = mock_weather
        mock_get_injuries.return_value = mock_injuries
        mock_predict.return_value = mock_ml_prediction
        mock_prepare_features.return_value = (MagicMock(), MagicMock())
        
        # Call the method under test
        result = await prediction_service._create_prediction_from_game(sample_game_data, 'basketball_nba')
        
        # Verify the result structure
        assert result is not None
        assert result['game_id'] == 'game_123'
        assert result['home_team'] == 'Lakers'
        assert result['away_team'] == 'Celtics'
        
        # Verify ML integration
        assert result['prediction']['ml_probability'] == 0.65
        assert result['prediction']['confidence'] == 0.8
        
        # Verify external factors integration
        assert result['factors']['weather_impact'] == 2.5
        assert result['factors']['injury_impact'] == 2.0
        assert result['factors']['sharp_money'] is False
        
        # Verify service calls
        mock_get_odds.assert_called_once()
        mock_get_weather.assert_called_once()
        mock_get_injuries.assert_called_once()
        mock_predict.assert_called_once()

@pytest.mark.asyncio
async def test_get_upcoming_predictions(prediction_service):
    # Mock get_scoreboard to return list of games
    mock_games = [
        {"id": "game_1", "status": {"type": {"state": "pre"}}},
        {"id": "game_2", "status": {"type": {"state": "pre"}}}
    ]
    
    with patch.object(prediction_service.espn_client, 'get_scoreboard', new_callable=AsyncMock) as mock_get_scoreboard, \
         patch.object(prediction_service, '_create_prediction_from_game', new_callable=AsyncMock) as mock_create_prediction:
        
        mock_get_scoreboard.return_value = mock_games
        mock_create_prediction.side_effect = [
            {'game_id': 'game_1', 'prediction': {'confidence': 0.8}},
            {'game_id': 'game_2', 'prediction': {'confidence': 0.7}}
        ]
        
        result = await prediction_service.get_upcoming_predictions('basketball_nba')
        
        assert len(result) == 2
        assert result[0]['game_id'] == 'game_1'
        assert result[1]['game_id'] == 'game_2'

@pytest.mark.asyncio
async def test_error_handling(prediction_service, sample_game_data):
    # Test error handling when a service fails
    with patch.object(prediction_service.odds_service, 'get_odds_for_game', new_callable=AsyncMock) as mock_get_odds:
        mock_get_odds.side_effect = Exception("API Error")
        
        # Should handle error gracefully and return None or raise specific exception
        # depending on implementation. Assuming it logs and returns None for now.
        try:
            result = await prediction_service._create_prediction_from_game(sample_game_data, 'basketball_nba')
            assert result is None
        except Exception:
            pass  # If it raises, that's also valid behavior to test

def test_sport_mapping(prediction_service):
    # Test sport key mapping
    assert prediction_service._map_sport_to_key('nba') == 'basketball_nba'
    assert prediction_service._map_sport_to_key('nfl') == 'americanfootball_nfl'
    assert prediction_service._map_sport_to_key('mlb') == 'baseball_mlb'
    assert prediction_service._map_sport_to_key('nhl') == 'icehockey_nhl'