import asyncio
import sys
sys.path.append('/app')
from app.database import engine
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def main():
    async with AsyncSession(engine) as session:
        for q in [
            'SELECT COUNT(*) FROM player_records',
            'SELECT COUNT(*) FROM player_game_logs'
        ]:
            result = await session.execute(text(q))
            print(result.scalar())

if __name__ == '__main__':
    asyncio.run(main())