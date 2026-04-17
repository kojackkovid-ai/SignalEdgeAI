#!/usr/bin/env python3
"""
Deep dive into why Club100 returns 0 players
"""
import asyncio
import sys
import json
sys.path.insert(0, '.')

async def debug():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy import select, text
    from app.models.prediction_records import PlayerGameLog, PlayerRecord
    
    DATABASE_URL = "sqlite+aiosqlite:///./sports_predictions.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_local = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_local() as db:
        print("=" * 80)
        print("BACKEND DATABASE DEEP DIVE")
        print("=" * 80)
        
        # Check players
        result = await db.execute(select(PlayerRecord))
        players = result.scalars().all()
        print(f"\n1. PlayerRecord table: {len(players)} records")
        for p in players[:3]:
            print(f"   - {p.id}: {p.name}")
        
        # Check game logs for NBA
        print(f"\n2. NBA game logs:")
        result = await db.execute(
            select(PlayerGameLog)
            .where(PlayerGameLog.sport_key == "basketball_nba")
            .limit(5)
        )
        logs = result.scalars().all()
        print(f"   Found {len(logs)} logs")
        
        for log in logs:
            print(f"\n   Player ID: {log.player_id} (type: {type(log.player_id).__name__})")
            print(f"   Stats type: {type(log.stats).__name__}")
            print(f"   Stats value: {log.stats}")
            
            # Try to parse stats
            if log.stats:
                try:
                    if isinstance(log.stats, str):
                        parsed = json.loads(log.stats)
                    else:
                        parsed = log.stats
                    print(f"   Parsed stats: {parsed}")
                except Exception as e:
                    print(f"   ERROR parsing: {e}")
            
            # Try to find player
            result = await db.execute(
                select(PlayerRecord).where(PlayerRecord.id == log.player_id)
            )
            player = result.scalar_one_or_none()
            if player:
                print(f"   ✓ Found player: {player.name}")
            else:
                print(f"   ✗ NO PLAYER FOUND for ID {log.player_id}!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug())
