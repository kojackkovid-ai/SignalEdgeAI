#!/usr/bin/env python3
"""
Test ESPN service directly
"""

import asyncio
import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.espn_prediction_service import ESPNPredictionService

async def test():
    service = ESPNPredictionService()
    try:
        print('Testing ESPN service...')
        games = await service.get_predictions('basketball_nba')
        print(f'Found {len(games)} NBA games')
        
        if games:
            print(f'First game: {games[0]["matchup"]}')
            print(f'Event ID: {games[0]["event_id"]}')
            
            # Test team stats first
            print('Testing team stats...')
            team_stats = await service.get_team_stats('basketball_nba', '8')  # Pistons team ID
            print(f'Pistons team stats: {team_stats}')
            
            props = await service.get_player_props('basketball_nba', games[0]['event_id'])
            print(f'Found {len(props)} player props')
            
            if props:
                print(f'First prop: {props[0]["player"]} - {props[0]["prediction"]}')
            else:
                print('No props returned')
        else:
            print('No games found')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test())