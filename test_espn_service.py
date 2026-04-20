#!/usr/bin/env python3
"""
Direct test of ESPN service for soccer props generation
Bypassing API layer to test the service directly
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.espn_prediction_service import ESPNPredictionService
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_soccer_props():
    """Test soccer props generation directly"""
    service = ESPNPredictionService()
    
    # Get upcoming EPL games
    print("\n=== FETCHING EPL GAMES ===")
    try:
        games = await service.get_upcoming_games('soccer_epl')
        print(f"[OK] Found {len(games)} EPL games")
        
        if not games:
            print("[ERROR] No games found for EPL")
            return
        
        game = games[0]
        print(f"\nGame: {game.get('title')}")
        print(f"ID: {game.get('id')}")
        print(f"Date: {game.get('date')}")
        
        # Try to get props for first game
        print(f"\n=== FETCHING PROPS FOR {game.get('title')} ===")
        props = await service.get_player_props('soccer_epl', game.get('id'))
        print(f"[OK] Returned {len(props)} props")
        
        if props:
            print("\nFirst 5 props:")
            for prop in props[:5]:
                print(f"  - {prop.get('athlete_name')} ({prop.get('market_key')}): {prop.get('point')} @ {prop.get('odds')}")
        else:
            print("[ERROR] NO PROPS RETURNED - This is the bug!")
            
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_soccer_props())
