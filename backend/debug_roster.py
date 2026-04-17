"""
Debug script to check roster structure for NHL and MLB
"""
import asyncio
import sys
sys.path.insert(0, '.')
from app.services.espn_prediction_service import ESPNPredictionService
import json

async def debug_roster():
    service = ESPNPredictionService()
    
    # Test NHL roster
    print('=== NHL Roster Debug ===')
    try:
        # Get a game first
        games = await service.get_upcoming_games('icehockey_nhl')
        if games:
            game = games[0]
            home_team_id = game['home_team']['id']
            print(f'Fetching roster for team {home_team_id}...')
            
            # Fetch roster directly
            url = f"{service.BASE_URL}/hockey/nhl/teams/{home_team_id}/roster"
            response = await service.client.get(url)
            data = response.json()
            
            print(f'Keys in response: {list(data.keys())}')
            
            if 'athletes' in data:
                athletes = data['athletes']
                print(f'Athletes type: {type(athletes)}')
                if isinstance(athletes, list) and len(athletes) > 0:
                    print(f'First athlete keys: {list(athletes[0].keys())}')
                    print(f'First athlete: {json.dumps(athletes[0], indent=2)[:500]}')
            elif 'squad' in data:
                print(f'Squad type: {type(data["squad"])}')
                print(f'Squad sample: {json.dumps(data["squad"], indent=2)[:500]}')
    except Exception as e:
        print(f'NHL Error: {e}')
        import traceback
        traceback.print_exc()
    
    # Test MLB roster
    print('\n=== MLB Roster Debug ===')
    try:
        games = await service.get_upcoming_games('baseball_mlb')
        if games:
            game = games[0]
            home_team_id = game['home_team']['id']
            print(f'Fetching roster for team {home_team_id}...')
            
            url = f"{service.BASE_URL}/baseball/mlb/teams/{home_team_id}/roster"
            response = await service.client.get(url)
            data = response.json()
            
            print(f'Keys in response: {list(data.keys())}')
            
            if 'athletes' in data:
                athletes = data['athletes']
                print(f'Athletes type: {type(athletes)}')
                if isinstance(athletes, list) and len(athletes) > 0:
                    print(f'First athlete keys: {list(athletes[0].keys())}')
                    print(f'First athlete: {json.dumps(athletes[0], indent=2)[:500]}')
            elif 'squad' in data:
                print(f'Squad type: {type(data["squad"])}')
                print(f'Squad sample: {json.dumps(data["squad"], indent=2)[:500]}')
    except Exception as e:
        print(f'MLB Error: {e}')
        import traceback
        traceback.print_exc()
    
    await service.close()

if __name__ == '__main__':
    asyncio.run(debug_roster())
