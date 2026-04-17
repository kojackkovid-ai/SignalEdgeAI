import asyncio
from sqlalchemy import text
from app.database import engine

async def check():
    async with engine.begin() as conn:
        result = await conn.execute(text("PRAGMA table_info(users)"))
        columns = {row[1]: row[2] for row in result.fetchall()}
        print("Users table columns:")
        for col, typ in columns.items():
            print(f"  {col}: {typ}")

asyncio.run(check())
