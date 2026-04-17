#!/usr/bin/env python3
"""
Check which database the ORM is using
"""
import asyncio
import sys
import os
sys.path.insert(0, '.')

async def debug():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy import select, text, inspect
    from app.config import Settings
    from app.models.prediction_records import PlayerRecord
    
    settings = Settings()
    db_url = settings.database_url
    print(f"ORM Database URL: {db_url}")
    
    engine = create_async_engine(db_url, echo=False)
    
    async_session_local = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_local() as db:
        # Check raw SQL
        result = await db.execute(text("PRAGMA database_list"))
        for row in result.fetchall():
            print(f"  Database connection: {row}")
        
        # Check raw SELECT
        result = await db.execute(text("SELECT COUNT(*) FROM player_record"))
        count = result.scalar()
        print(f"\nRaw SQL COUNT: {count}")
        
        # Check ORM SELECT
        result = await db.execute(select(PlayerRecord))
        players = result.scalars().all()
        print(f"ORM SELECT: {len(players)} players")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug())
