"""Test Club 100 with actual SQLAlchemy models"""
import asyncio
import sys
sys.path.insert(0, 'sports-prediction-platform/backend')

from app.database import AsyncSessionLocal
from app.models.prediction_records import PlayerGameLog, PlayerRecord
from sqlalchemy import select

async def test():
    async with AsyncSessionLocal() as db:
        print("\n=== Testing with SQLAlchemy Models ===\n")
        
        # Test 1: Query player game logs
        print("1. Querying PlayerGameLog for basketball_nba...")
        stmt = select(PlayerGameLog).where(
            PlayerGameLog.sport_key == "basketball_nba"
        ).limit(10)
        result = await db.execute(stmt)
        logs = result.scalars().all()
        print(f"   Found {len(logs)} game logs")
        for log in logs[:2]:
            print(f"     Player ID: {log.player_id}, Stats: {log.stats}")
        
        # Test 2: Query players
        print("\n2. Querying PlayerRecord...")
        stmt = select(PlayerRecord)
        result = await db.execute(stmt)
        players = result.scalars().all()
        print(f"   Found {len(players)} players")
        for player in players:
            print(f"     ID: {player.id}, Name: {player.name}, Sport: {player.sport_key}")
        
        # Test 3: Check if player IDs match
        print("\n3. Checking if game log player IDs exist in PlayerRecord...")
        stmt = select(PlayerGameLog.player_id).distinct()
        result = await db.execute(stmt)
        player_ids = [row[0] for row in result.fetchall()]
        print(f"   Unique player IDs in game logs: {player_ids}")
        
        for player_id in player_ids:
            stmt = select(PlayerRecord).where(PlayerRecord.id == player_id)
            result = await db.execute(stmt)
            player = result.scalar_one_or_none()
            if player:
                print(f"     {player_id}: {player.name} - OK")
            else:
                print(f"     {player_id}: NOT FOUND - ERROR!")

if __name__ == "__main__":
    asyncio.run(test())
