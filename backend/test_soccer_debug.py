import asyncio
import sys
sys.path.insert(0, '.')
from app.services.espn_prediction_service import ESPNPredictionService

async def test_soccer():
    service = ESPNPredictionService()
    
    # Test soccer predictions
    print('=== Testing Soccer Predictions ===')
    try:
        predictions = await service.get_predictions(sport='soccer_epl', limit=3)
        print(f'Found {len(predictions)} soccer predictions')
        for p in predictions[:2]:
            print(f"  - {p.get('matchup', 'N/A')}: {p.get('prediction', 'N/A')}")
    except Exception as e:
        print(f"Error getting predictions: {e}")
        import traceback
        traceback.print_exc()
    
    # Test soccer player props
    print('\n=== Testing Soccer Player Props ===')
    try:
        games = await service.get_upcoming_games('soccer_epl')
        if games:
            print(f'Found {len(games)} soccer games')
            print(f"First game: {games[0].get('away_team', {}).get('name', 'N/A')} @ {games[0].get('home_team', {}).get('name', 'N/A')}")
            props = await service.get_player_props('soccer_epl', games[0]['id'])
            print(f'Generated {len(props)} player props')
            if props:
                print(f"Sample: {props[0].get('player', 'N/A')} - {props[0].get('prediction', 'N/A')}")
            else:
                print("No props generated - checking roster...")
                # Debug roster
                home_id = games[0].get('home_team', {}).get('id')
                away_id = games[0].get('away_team', {}).get('id')
                print(f"Home team ID: {home_id}, Away team ID: {away_id}")
                if home_id:
                    roster = await service._get_team_roster('soccer_epl', str(home_id))
                    print(f"Home roster size: {len(roster)}")
                    if roster:
                        print(f"First player: {roster[0]}")
        else:
            print('No soccer games found')
    except Exception as e:
        print(f"Error getting player props: {e}")
        import traceback
        traceback.print_exc()
    
    await service.close()

if __name__ == "__main__":
    asyncio.run(test_soccer())
