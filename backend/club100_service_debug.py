import asyncio
import sys
sys.path.insert(0, '.')
from app.database import get_db
from app.services.club_100_streak_service import get_club_100_streak_service
from app.services.espn_player_stats_service import get_player_stats_service
from app.models.db_models import User

async def debug_service():
    service = get_club_100_streak_service()
    espn_service = get_player_stats_service()
    async for db in get_db():
        for sport in ['nba', 'mlb', 'nhl', 'nfl']:
            print(f"=== {sport.upper()} ===")
            games = await espn_service.get_today_games_player_stats(sport)
            print(f"Today games: {len(games)}")
            if not games:
                continue
            streaks = await service._analyze_sport_streaks(db, sport, 3, games)
            print(f"Found streaks: {len(streaks)}")
            if streaks:
                print(streaks[0])
            print()
        break

if __name__ == '__main__':
    asyncio.run(debug_service())
