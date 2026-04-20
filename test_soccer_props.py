import json
import requests

try:
    # Get EPL games
    print('Fetching EPL games...')
    games_resp = requests.get('http://localhost:8000/api/games', params={'sport_key': 'soccer_epl'}, timeout=10)
    print(f'Games status: {games_resp.status_code}')
    games = games_resp.json()
    print(f'Found {len(games)} games')
    
    if games:
        game = games[0]
        print(f'Game ID: {game.get("id")}')
        print(f'Game: {game.get("title")}')
        
        # Try to get props
        print(f'\nFetching props for game {game.get("id")}...')
        props_resp = requests.get(f'http://localhost:8000/api/props/{game.get("id")}', 
                                  params={'sport_key': 'soccer_epl'}, timeout=10)
        print(f'Props status: {props_resp.status_code}')
        props = props_resp.json()
        print(f'Props count: {len(props)}')
        if props:
            print(json.dumps(props[:2], indent=2))
        else:
            print('NO PROPS RETURNED - This is the bug!')
    else:
        print('No games found')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
