#!/usr/bin/env python3
"""
Test ESPN team stats structure - detailed exploration
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
        
        # Let's get the raw response to see the structure
        import httpx
        async with httpx.AsyncClient() as client:
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/8"
            response = await client.get(url)
            data = response.json()
            
            print("\nLooking for stats in different locations...")
            
            # Check the main team object
            team = data.get('team', {})
            print(f"team.keys(): {list(team.keys())}")
            
            # Check if there are any stats anywhere
            def find_stats(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if 'stat' in key.lower():
                            print(f"Found 'stat' in key: {path}.{key} = {value}")
                        elif isinstance(value, (dict, list)):
                            find_stats(value, f"{path}.{key}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        if isinstance(item, (dict, list)):
                            find_stats(item, f"{path}[{i}]")
            
            find_stats(data, "data")
            
            # Also check if there's a specific stats endpoint
            print("\nTrying different endpoints...")
            
            # Try the team stats endpoint
            stats_url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/8/statistics"
            try:
                stats_response = await client.get(stats_url)
                if stats_response.status_code == 200:
                    stats_data = stats_response.json()
                    print(f"Stats endpoint found! Keys: {list(stats_data.keys())}")
                    if 'statistics' in stats_data:
                        print(f"Statistics structure: {type(stats_data['statistics'])}")
                        if isinstance(stats_data['statistics'], list) and len(stats_data['statistics']) > 0:
                            print(f"First stat item: {stats_data['statistics'][0]}")
                else:
                    print(f"Stats endpoint returned: {stats_response.status_code}")
            except Exception as e:
                print(f"Stats endpoint error: {e}")
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test())