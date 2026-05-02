#!/usr/bin/env python3
"""Simple test to check if Club 100 is working"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.club_100_service import Club100Service
from app.database import get_db
import asyncio

async def test_club100():
    """Test Club 100 service directly"""
    async for db in get_db():
        service = Club100Service()
        try:
            data = await service.get_club_100_data(db)
            print("✅ Club 100 service returned data!")

            for sport, players in data.items():
                print(f"{sport.upper()}: {len(players)} players")
                if players:
                    print(f"Sample: {players[0]}")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_club100())