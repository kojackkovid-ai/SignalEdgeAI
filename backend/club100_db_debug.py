import asyncio
import sys
sys.path.insert(0, '.')
from app.database import get_db
from sqlalchemy import text

async def main():
    async for session in get_db():
        print('connected')
        result = await session.execute(text("SELECT DISTINCT sport_key, COUNT(*) FROM player_records GROUP BY sport_key ORDER BY COUNT(*) DESC"))
        print('player_records sport_key counts:')
        for row in result.fetchall():
            print(row)
        result = await session.execute(text("SELECT DISTINCT sport_key, COUNT(*) FROM player_game_logs GROUP BY sport_key ORDER BY COUNT(*) DESC"))
        print('player_game_logs sport_key counts:')
        for row in result.fetchall():
            print(row)
        result = await session.execute(text("SELECT COUNT(*) FROM player_game_logs WHERE date >= CURRENT_DATE - INTERVAL '30 days'"))
        print('recent logs 30 days:', result.scalar())
        break

asyncio.run(main())
