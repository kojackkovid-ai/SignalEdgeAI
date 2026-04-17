
import asyncio
import logging
from app.services.espn_prediction_service import ESPNPredictionService

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_soccer_props():
    service = ESPNPredictionService()
    
    # Mock data
    athletes = [
        {"displayName": "Erling Haaland", "position": {"abbreviation": "ST"}, "id": "1"},
        {"displayName": "Kevin De Bruyne", "position": {"abbreviation": "CM"}, "id": "2"},
        {"displayName": "Ruben Dias", "position": {"abbreviation": "CB"}, "id": "3"},
        {"displayName": "Unknown Player", "position": {"abbreviation": "UNK"}, "id": "4"}
    ]
    
    team_stats = {
        "goals_per_game": 2.5,
        "assists_per_game": 1.8,
        "shots_per_game": 15.0
    }
    
    team_name = "Manchester City"
    sport_key = "soccer_epl"
    event_id = "12345"
    game_data = {"id": "12345", "competitions": [{"competitors": [{"homeAway": "home", "team": {"displayName": "Man City"}}, {"homeAway": "away", "team": {"displayName": "Arsenal"}}]}]}
    injuries = []
    
    print("Testing soccer player props generation...")
    
    try:
        props = await service._generate_soccer_player_props(
            athletes, team_stats, team_name, sport_key, event_id, game_data, injuries
        )
        
        print(f"Generated {len(props)} props")
        for prop in props:
            print(f"- {prop['player']} ({prop['market_key']}): {prop['point']} (Prediction: {prop['prediction']})")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_soccer_props())
