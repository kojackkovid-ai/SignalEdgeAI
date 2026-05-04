import asyncio
import sys
sys.path.insert(0, '.')
from app.database import get_db
from app.services.espn_player_stats_service import get_player_stats_service
from app.services.club_100_streak_service import Club100StreakService
from app.models.db_models import User
from app.models.prediction_records import PlayerRecord, PlayerGameLog
from sqlalchemy import select

SPORTS = ['nba', 'mlb', 'nhl', 'nfl']

async def debug_mapping():
    service = Club100StreakService()
    espn_service = get_player_stats_service()
    async for db in get_db():
        for sport in SPORTS:
            print(f"=== {sport.upper()} ===")
            games = await espn_service.get_today_games_player_stats(sport)
            print(f"Today games: {len(games)}")
            today_dict = service._build_today_games_dict(sport, games)
            print(f"Players in today dict: {len(today_dict)}")
            sample = list(today_dict.items())[:10]
            for aid, games_list in sample:
                print(f"  athlete_id={aid}, games={games_list}")
            # count DB players with external ids for sport
            id_field = {
                'nba': PlayerRecord.nba_id,
                'mlb': PlayerRecord.mlb_id,
                'nhl': PlayerRecord.nhl_id,
                'nfl': PlayerRecord.nfl_id,
            }[sport]
            stmt = select(PlayerRecord).where(id_field != None)
            res = await db.execute(stmt)
            all_records = res.scalars().all()
            print(f"DB players with {sport}_id: {len(all_records)}")
            # query for sample athletes
            for aid, _ in sample:
                stmt2 = select(PlayerRecord).where(id_field == aid)
                res2 = await db.execute(stmt2)
                player = res2.scalar_one_or_none()
                print(f"   athlete_id={aid} -> {'FOUND '+player.name if player else 'NOT FOUND'}")
            if sample:
                print('---')
        break

if __name__ == '__main__':
    asyncio.run(debug_mapping())
