"""Test MLB player props"""
import asyncio
import logging
from app.services.espn_prediction_service import ESPNPredictionService

logging.basicConfig(level=logging.INFO)

async def test():
    service = ESPNPredictionService()
    
    print('Getting MLB games...')
    games = await service.get_upcoming_games('baseball_mlb')
    print(f'Found {len(games)} games')
    
    if not games:
        print('No games found!')
        return
    
    game = games[0]
    game_id = game['id']
    print(f'Testing props for game {game_id}')
    
    props = await service.get_player_props('baseball_mlb', game_id)
    print(f'Props returned: {len(props)}')
    
    if props:
        for p in props[:3]:
            player = p.get('player')
            pred = p.get('prediction')
            print(f'  - {player}: {pred}')
    else:
        print('  No props generated!')
        
        # Debug: try to get roster
        print('Debugging roster fetch...')
        home_id = game['home_team']['id']
        roster = await service._get_team_roster('baseball_mlb', str(home_id))
        print(f'Home roster: {len(roster)} players')
        if roster:
            print(f'  Sample: {roster[0]}')

asyncio.run(test())
