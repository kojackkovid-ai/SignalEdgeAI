#!/usr/bin/env python3
"""
Test ESPN team stats structure
"""

import asyncio
import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.espn_prediction_service import ESPNPredictionService

async def test():
    service = ESPNPredictionService()
    try:
        print('Testing ESPN team stats structure...')
        
        # Get Pistons team stats
        team_stats = await service.get_team_stats('basketball_nba', '8')  # Pistons team ID
        print(f'Pistons team stats: {team_stats}')
        
        # Let's also get the raw response to see the structure
        import httpx
        async with httpx.AsyncClient() as client:
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/8"
            response = await client.get(url)
            data = response.json()
            
            print("\nRaw team data structure:")
            print(json.dumps(data, indent=2))
            
            # Look for stats in different locations
            print("\nLooking for stats...")
            print(f"team.get('record'): {data.get('record')}")
            print(f"team.get('statistics'): {data.get('statistics')}")
            print(f"team.get('stats'): {data.get('stats')}")
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test())