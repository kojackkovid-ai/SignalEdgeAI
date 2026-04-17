"""
Test live player props for NHL, MLB, and NBA to verify functionality
"""
import asyncio
import sys
sys.path.insert(0, '.')
from app.services.espn_prediction_service import ESPNPredictionService

async def test_props():
    service = ESPNPredictionService()
    
    # Test NHL
    print('=== Testing NHL ===')
    try:
        games = await service.get_upcoming_games('icehockey_nhl')
        print(f'Found {len(games)} NHL games')
        if games:
            game = games[0]
            game_id = game.get('id', 'unknown')
            print(f'Testing game: {game_id}')
            props = await service.get_player_props('icehockey_nhl', game_id)
            print(f'Generated {len(props)} NHL props')
            for p in props[:3]:
                print(f'  - {p.get("player", "N/A")}: {p.get("prediction", "N/A")}')
        else:
            print('No NHL games found - may be off-season')
    except Exception as e:
        print(f'NHL Error: {e}')
        import traceback
        traceback.print_exc()
    
    # Test MLB
    print('\n=== Testing MLB ===')
    try:
        games = await service.get_upcoming_games('baseball_mlb')
        print(f'Found {len(games)} MLB games')
        if games:
            game = games[0]
            game_id = game.get('id', 'unknown')
            print(f'Testing game: {game_id}')
            props = await service.get_player_props('baseball_mlb', game_id)
            print(f'Generated {len(props)} MLB props')
            for p in props[:3]:
                print(f'  - {p.get("player", "N/A")}: {p.get("prediction", "N/A")}')
        else:
            print('No MLB games found - may be off-season')
    except Exception as e:
        print(f'MLB Error: {e}')
        import traceback
        traceback.print_exc()
    
    # Test NBA
    print('\n=== Testing NBA ===')
    try:
        games = await service.get_upcoming_games('basketball_nba')
        print(f'Found {len(games)} NBA games')
        if games:
            game = games[0]
            game_id = game.get('id', 'unknown')
            print(f'Testing game: {game_id}')
            props = await service.get_player_props('basketball_nba', game_id)
            print(f'Generated {len(props)} NBA props')
            for p in props[:3]:
                print(f'  - {p.get("player", "N/A")}: {p.get("prediction", "N/A")}')
        else:
            print('No NBA games found')
    except Exception as e:
        print(f'NBA Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_props())
