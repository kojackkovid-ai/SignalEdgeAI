import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.odds_service import RealOddsService

@pytest.fixture
def odds_service():
    return RealOddsService(api_key="test_key")

@pytest.fixture
def mock_odds_response():
    return [
        {
            "id": "game_123",
            "sport_key": "basketball_nba",
            "home_team": "Lakers",
            "away_team": "Celtics",
            "commence_time": "2024-01-15T20:00:00Z",
            "bookmakers": [
                {
                    "key": "draftkings",
                    "title": "DraftKings",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Lakers", "price": -150},
                                {"name": "Celtics", "price": 130}
                            ]
                        },
                        {
                            "key": "spreads",
                            "outcomes": [
                                {"name": "Lakers", "point": -3.5, "price": -110},
                                {"name": "Celtics", "point": 3.5, "price": -110}
                            ]
                        }
                    ]
                },
                {
                    "key": "fanduel",
                    "title": "FanDuel",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Lakers", "price": -145},
                                {"name": "Celtics", "price": 125}
                            ]
                        }
                    ]
                }
            ]
        }
    ]

@pytest.mark.asyncio
async def test_get_odds_for_game(odds_service, mock_odds_response):
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_odds_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await odds_service.get_odds_for_game('basketball_nba', 'game_123')
        
        assert result is not None
        assert 'moneyline' in result
        assert 'spread' in result
        assert 'total' in result
        assert 'line_movement' in result
        assert 'sharp_money_indicators' in result

def test_calculate_implied_probability(odds_service):
    # Test American odds conversion
    assert odds_service._calculate_implied_probability(-110) == pytest.approx(0.523, rel=0.01)
    assert odds_service._calculate_implied_probability(110) == pytest.approx(0.476, rel=0.01)
    assert odds_service._calculate_implied_probability(-200) == pytest.approx(0.667, rel=0.01)
    assert odds_service._calculate_implied_probability(200) == pytest.approx(0.333, rel=0.01)

def test_calculate_line_movement(odds_service):
    # Test line movement calculation
    opening_line = {"price": -110, "point": -3.5}
    current_line = {"price": -120, "point": -4.5}
    
    movement = odds_service._calculate_line_movement(opening_line, current_line)
    
    assert movement['price_change'] == -10
    assert movement['point_change'] == -1.0
    assert movement['movement_percentage'] == pytest.approx(9.09, rel=0.01)

def test_detect_sharp_money_indicators(odds_service):
    # Test sharp money detection
    odds_data = [
        {"price": -110, "point": -3.5, "bookmaker": "draftkings"},
        {"price": -120, "point": -4.0, "bookmaker": "pinnacle"},
        {"price": -115, "point": -3.5, "bookmaker": "fanduel"},
        {"price": -125, "point": -4.0, "bookmaker": "bet365"}
    ]
    
    indicators = odds_service._detect_sharp_money_indicators(odds_data)
    
    assert 'line_consensus' in indicators
    assert 'sharp_line_detected' in indicators
    assert 'reverse_line_movement' in indicators

def test_calculate_arbitrage_opportunities(odds_service):
    # Test arbitrage detection
    odds_data = [
        {"price": -110, "point": -3.5, "bookmaker": "draftkings", "side": "home"},
        {"price": 120, "point": 3.5, "bookmaker": "fanduel", "side": "away"}
    ]
    
    arbitrage = odds_service._calculate_arbitrage_opportunities(odds_data)
    
    assert 'arbitrage_available' in arbitrage
    assert 'profit_percentage' in arbitrage
    assert 'required_stakes' in arbitrage

@pytest.mark.asyncio
async def test_get_historical_odds(odds_service, mock_odds_response):
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_odds_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await odds_service.get_historical_odds('basketball_nba', 'game_123', '2024-01-15')
        
        assert result is not None
        assert 'opening_lines' in result
        assert 'closing_lines' in result
        assert 'line_movement_history' in result

def test_analyze_betting_markets(odds_service):
    # Test market analysis
    odds_data = {
        'moneyline': {
            'home_odds': -150,
            'away_odds': 130,
            'home_implied_prob': 0.6,
            'away_implied_prob': 0.435
        },
        'spread': {
            'home_spread': -3.5,
            'away_spread': 3.5,
            'home_odds': -110,
            'away_odds': -110
        }
    }
    
    analysis = odds_service._analyze_betting_markets(odds_data)
    
    assert 'market_efficiency' in analysis
    assert 'vig_percentage' in analysis
    assert 'value_opportunities' in analysis