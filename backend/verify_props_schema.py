
import asyncio
import sys
import logging
from datetime import datetime
from typing import List, Optional

# Mock the environment and dependencies
import sys
from unittest.mock import MagicMock

# Mock app.config.settings
sys.modules['app.config'] = MagicMock()
sys.modules['app.config'].settings.odds_api_key = "test_key"

# Import the service (this will import ml_service too)
# We need to ensure app.services.ml_service is available or mocked if it imports other things
# ml_service imports numpy, pandas, tensorflow etc. simpler to let it import if installed, 
# but if not installed, we might fail. Assuming they are installed in the environment.

try:
    from app.services.odds_api_service import OddsApiService
    from app.services.ml_service import MLService
except ImportError:
    # If we can't import due to missing deps in this env, we mock them
    print("Could not import services directly, ensure you are in the right environment.")
    sys.exit(1)

# Pydantic model for validation
from pydantic import BaseModel
from typing import List, Optional

class ReasoningPoint(BaseModel):
    factor: str
    impact: str
    weight: float
    explanation: str

class ModelEnsemble(BaseModel):
    name: str
    prediction: str
    confidence: float
    weight: float

class PredictionResponse(BaseModel):
    id: str
    sport: str
    league: str
    matchup: str
    game_time: Optional[str] = None
    prediction: str
    confidence: float
    prediction_type: str
    created_at: str
    odds: Optional[str] = None
    reasoning: Optional[List[ReasoningPoint]] = None
    models: Optional[List[ModelEnsemble]] = None
    resolved_at: Optional[str] = None
    result: Optional[str] = None
    player: Optional[str] = None
    market_key: Optional[str] = None
    point: Optional[float] = None
    sport_key: Optional[str] = None
    event_id: Optional[str] = None
    is_locked: Optional[bool] = True

async def test_get_player_props():
    service = OddsApiService()
    
    # Mock get_event_odds to return sample data
    # We want to test logic inside get_player_props, so we mock the external API call
    service.get_event_odds = MagicMock()
    
    # Sample response from OddsAPI for player props
    sample_data = {
        "id": "event_123",
        "sport_key": "basketball_nba",
        "commence_time": "2023-10-27T23:00:00Z",
        "home_team": "Los Angeles Lakers",
        "away_team": "Phoenix Suns",
        "bookmakers": [
            {
                "key": "draftkings",
                "markets": [
                    {
                        "key": "player_points",
                        "outcomes": [
                            {"name": "LeBron James", "description": "Over", "point": 25.5, "price": -110},
                            {"name": "LeBron James", "description": "Under", "point": 25.5, "price": -110}
                        ]
                    }
                ]
            }
        ]
    }
    
    # Mock the awaitable
    f = asyncio.Future()
    f.set_result(sample_data)
    service.get_event_odds.return_value = f

    print("Testing get_player_props...")
    props = await service.get_player_props("basketball_nba", "event_123")
    
    print(f"Got {len(props)} props")
    
    if not props:
        print("ERROR: No props returned")
        return

    prop = props[0]
    print("Sample Prop:", prop)
    
    # Validate against Pydantic model
    try:
        model = PredictionResponse(**prop)
        print("✅ Validation Successful!")
        print(model.json(indent=2))
    except Exception as e:
        print("❌ Validation Failed!")
        print(e)

if __name__ == "__main__":
    asyncio.run(test_get_player_props())
