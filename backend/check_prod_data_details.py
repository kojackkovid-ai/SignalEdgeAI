import asyncio
import sys
sys.path.append('/app')
from app.database import engine
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def main():
    async with AsyncSession(engine) as session:
        result = await session.execute(text("SELECT sport_key, COUNT(*) FROM player_records GROUP BY sport_key ORDER BY COUNT(*) DESC"))
        for row in result:
            print(row)
        result = await session.execute(text("SELECT sport_key, COUNT(*) FROM player_game_logs GROUP BY sport_key ORDER BY COUNT(*) DESC"))
        # If game logs has no sport_key, only show total count
        print('---game logs totals---')
        print(result.fetchall())

if __name__ == '__main__':
    asyncio.run(main())