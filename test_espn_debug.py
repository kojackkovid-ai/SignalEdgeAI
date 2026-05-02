#!/usr/bin/env python3
"""Test ESPN player stats service to debug Club 100 data issues"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.espn_player_stats_service import get_player_stats_service

async def test_espn_service():
    """Test the ESPN service for each sport"""
    service = get_player_stats_service()

    sports = ['nba', 'nfl', 'mlb', 'nhl', 'soccer']

    for sport in sports:
        print(f"\n=== Testing {sport.upper()} ===")
        try:
            stats = await service.get_today_games_player_stats(sport)
            print(f"Got {len(stats)} player stats for {sport}")
            if stats:
                print(f"Sample player: {stats[0]}")
            else:
                print("No player stats returned")
        except Exception as e:
            print(f"Error getting {sport} stats: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_espn_service())