
import asyncio
import logging
from datetime import datetime
from app.services.odds_api_service import OddsApiService

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_props_fix():
    print("--- Testing Player Props Fix ---")
    odds_service = OddsApiService()
    
    # Mock Event Data with Props
    mock_event_with_props = {
        "id": "test_event_props",
        "sport_key": "basketball_nba",
        "home_team": "Lakers",
        "away_team": "Celtics",
        "commence_time": "2024-02-04T00:00:00Z",
        "bookmakers": [
            {
                "key": "fanduel",
                "markets": [
                    {
                        "key": "player_points",
                        "outcomes": [
                            {"name": "LeBron James", "point": 25.5, "price": -115, "description": "Over"},
                            {"name": "LeBron James", "point": 25.5, "price": -105, "description": "Under"}
                        ]
                    }
                ]
            }
        ]
    }
    
    # We need to mock get_event_odds to return our mock data
    # Monkey patch the method
    async def mock_get_event_odds(sport_key, event_id, markets):
        print(f"Mock fetching odds for {event_id}...")
        return mock_event_with_props
        
    odds_service.get_event_odds = mock_get_event_odds
    
    print("Calling get_player_props...")
    props = await odds_service.get_player_props("basketball_nba", "test_event_props")
    
    if props:
        print(f"\n✅ Received {len(props)} props")
        p = props[0]
        print("Sample Prop Data:")
        print(f"- Player: {p.get('player')}")
        print(f"- Prediction: {p.get('prediction')}")
        print(f"- Odds: {p.get('odds')} (Type: {type(p.get('odds'))})")
        print(f"- Matchup: {p.get('matchup')}")
        print(f"- Sport: {p.get('sport')}")
        print(f"- League: {p.get('league')}")
        
        # Verify required fields for Pydantic model
        required_fields = ['id', 'sport', 'league', 'matchup', 'prediction', 'confidence', 'prediction_type', 'created_at']
        missing = [f for f in required_fields if f not in p]
        
        if not missing:
            print("\n✅ All required fields present")
        else:
            print(f"\n❌ Missing fields: {missing}")
            
        if isinstance(p.get('odds'), str):
             print("✅ Odds is string")
        else:
             print(f"❌ Odds is not string: {type(p.get('odds'))}")
             
    else:
        print("❌ No props returned")

if __name__ == "__main__":
    asyncio.run(test_props_fix())
