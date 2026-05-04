import asyncio
import sys
sys.path.insert(0, '.')
from app.services.espn_player_stats_service import get_player_stats_service

async def main():
    service = get_player_stats_service()
    games = await service.get_today_games_player_stats('nfl')
    print('games', len(games))
    if games:
        import json
        print(json.dumps(games[0]['leaders'][:50], indent=2))

if __name__ == '__main__':
    asyncio.run(main())
