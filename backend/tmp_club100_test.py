import os
import sys
import asyncio

os.environ['SECRET_KEY'] = 'localtestkey1234567890123456789012'
os.environ['USE_SQLITE'] = 'true'
sys.path.insert(0, 'backend')

from app.services.club_100_streak_service import Club100StreakService
from app.database import get_db

async def main():
    service = Club100StreakService()
    async for db in get_db():
        data = await service.get_club_100_streaks(db, min_streak_length=2, force_refresh=True)
        print({k: len(v) for k, v in data.items()})
        print(data)
        break

asyncio.run(main())
