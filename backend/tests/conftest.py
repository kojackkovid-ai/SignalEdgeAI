import pytest
import os
import sys
from pathlib import Path

# Add the backend directory to the python path
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

@pytest.fixture(scope="session")
def mock_env_vars():
    """Set up mock environment variables for testing"""
    os.environ["ODDS_API_KEY"] = "test_odds_key"
    os.environ["OPENWEATHER_API_KEY"] = "test_weather_key"
    os.environ["ESPN_API_KEY"] = "test_espn_key"
    yield
    # Clean up
    if "ODDS_API_KEY" in os.environ:
        del os.environ["ODDS_API_KEY"]
    if "OPENWEATHER_API_KEY" in os.environ:
        del os.environ["OPENWEATHER_API_KEY"]
    if "ESPN_API_KEY" in os.environ:
        del os.environ["ESPN_API_KEY"]

@pytest.fixture
def mock_game_data():
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
