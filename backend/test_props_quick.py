import asyncio
import sys
sys.path.insert(0, '.')

from app.services.espn_prediction_service import ESPNPredictionService

async def test():
    service = ESPNPredictionService()
    
    # Get upcoming NBA games
    print("Fetching NBA games...")
    games = await service.get_upcoming_games('basketball_nba')
    print(f'Found {len(games)} NBA games')
    
    if games:
        game = games[0]
        print(f'First game: {game.get("id")} - {game.get("home_team", {}).get("name")} vs {game.get("away_team", {}).get("name")}')
        
        # Try to get player props for the first game
        event_id = game['id']
        print(f'Getting props for event {event_id}...')
        
        props = await service.get_player_props('basketball_nba', event_id)
        print(f'Got {len(props)} props')
        
        if props:
            print('Sample prop:', props[0])
        else:
            print('No props returned - checking why...')
    else:
        print('No games found - trying different sport')
        
        # Try NHL
        games = await service.get_upcoming_games('icehockey_nhl')
        print(f'Found {len(games)} NHL games')
        
        if games:
            game = games[0]
            event_id = game['id']
            print(f'Getting props for NHL event {event_id}...')
            props = await service.get_player_props('icehockey_nhl', event_id)
            print(f'Got {len(props)} NHL props')
            if props:
                print('Sample NHL prop:', props[0])

if __name__ == "__main__":
    asyncio.run(test())
