import asyncio
import sys
sys.path.insert(0, '.')
from app.services.espn_prediction_service import ESPNPredictionService

async def test():
    service = ESPNPredictionService()
    
    # Test NBA predictions
    print('=== Testing NBA Predictions ===')
    try:
        games = await service.get_upcoming_games('basketball_nba')
        print(f'Games found: {len(games)}')
        for g in games[:3]:
            print(f'  Game: {g.get("id")} - {g.get("home_team", {}).get("name")} vs {g.get("away_team", {}).get("name")}')
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test getting predictions
    print('=== Testing get_predictions ===')
    try:
        preds = await service.get_predictions(sport='basketball_nba', limit=3)
        print(f'Predictions found: {len(preds)}')
        for p in preds[:3]:
            print(f'  Prediction: {p.get("id")} - {p.get("matchup")} - {p.get("prediction")} ({p.get("confidence")}%)')
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test player props if we have a game
    print('=== Testing Player Props ===')
    try:
        if games:
            game_id = games[0].get('id')
            print(f'Testing props for game: {game_id}')
            props = await service.get_player_props('basketball_nba', game_id)
            print(f'Props found: {len(props)}')
            for prop in props[:3]:
                print(f'  Prop: {prop.get("id")} - {prop.get("player")} - {prop.get("market_key")} - {prop.get("prediction")}')
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        
    await service.close()

if __name__ == '__main__':
    asyncio.run(test())
