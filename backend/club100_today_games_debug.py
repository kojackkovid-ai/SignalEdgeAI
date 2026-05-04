import asyncio
import sys
sys.path.insert(0, '.')
from app.services.espn_player_stats_service import get_player_stats_service

async def main():
    service = get_player_stats_service()
    for sport in ['nba', 'mlb', 'nhl', 'nfl']:
        print(f"=== Testing Today's {sport.upper()} Games ===")
        try:
            games = await service.get_today_games_player_stats(sport)
            print(f"Found {len(games)} games")
            for i, game in enumerate(games[:3], start=1):
                print(f"Game {i}: {game.get('game', {}).get('name')}")
                print(f"  home: {game.get('home_team', {}).get('name')} ({game.get('home_team', {}).get('id')})")
                print(f"  away: {game.get('away_team', {}).get('name')} ({game.get('away_team', {}).get('id')})")
                print(f"  leaders: {len(game.get('leaders', []))}")
                if not game.get('leaders'):
                    print(f"  no leaders, roster attached: {len(game.get('home_team', {}).get('leaders', [])) + len(game.get('away_team', {}).get('leaders', []))}")
                else:
                    print('  sample leader:', game.get('leaders')[0].get('athlete', {}).get('fullName'))
        except Exception as e:
            print('Error:', type(e).__name__, e)
        print()

asyncio.run(main())
