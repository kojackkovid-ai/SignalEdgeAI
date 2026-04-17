#!/usr/bin/env python3
"""
Test ESPN team statistics endpoint
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
        print('Testing ESPN team statistics endpoint...')
        
        # Let's get the statistics endpoint
        import httpx
        async with httpx.AsyncClient() as client:
            stats_url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/8/statistics"
            stats_response = await client.get(stats_url)
            stats_data = stats_response.json()
            
            print(f"Statistics endpoint status: {stats_response.status_code}")
            print(f"Statistics keys: {list(stats_data.keys())}")
            
            if 'results' in stats_data:
                print(f"Results type: {type(stats_data['results'])}")
                if isinstance(stats_data['results'], list) and len(stats_data['results']) > 0:
                    print(f"First result keys: {list(stats_data['results'][0].keys())}")
                    print(f"First result: {json.dumps(stats_data['results'][0], indent=2)}")
            
            # Also check the stats from the main team endpoint
            print("\n" + "="*50)
            print("Stats from main team endpoint:")
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/8"
            response = await client.get(url)
            data = response.json()
            
            team = data.get('team', {})
            record_items = team.get('record', {}).get('items', [])
            if record_items:
                stats = record_items[0].get('stats', [])
                print(f"Found {len(stats)} stats:")
                for stat in stats:
                    print(f"  {stat['name']}: {stat['value']}")
                    
                # Find the key stats we need
                key_stats = {
                    'avgPointsFor': None,
                    'avgPointsAgainst': None,
                    'differential': None,
                    'winPercent': None
                }
                
                for stat in stats:
                    if stat['name'] in key_stats:
                        key_stats[stat['name']] = stat['value']
                
                print(f"\nKey stats for Pistons:")
                for name, value in key_stats.items():
                    print(f"  {name}: {value}")
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test())