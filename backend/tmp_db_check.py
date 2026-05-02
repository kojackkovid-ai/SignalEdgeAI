import asyncio
from app.database import get_async_session
from app.models.prediction_records import PlayerRecord, PlayerGameLog
from sqlalchemy import select, func

async def main():
    async with await get_async_session() as session:
        result = await session.execute(select(func.count()).select_from(PlayerRecord))
        print('PlayerRecord count:', result.scalar_one())
        result = await session.execute(select(PlayerRecord).where(PlayerRecord.nba_id != None).limit(5))
        rows = result.scalars().all()
        print('Sample with nba_id:', len(rows))
        for r in rows:
            print(r.id, r.name, r.sport_key, r.nba_id)
        result = await session.execute(select(func.count()).select_from(PlayerGameLog))
        print('PlayerGameLog count:', result.scalar_one())

asyncio.run(main())
