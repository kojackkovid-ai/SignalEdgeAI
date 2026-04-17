#!/usr/bin/env python3
"""Quick debug script to see what ESPN API is returning"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta

async def debug_espn():
    """Debug the ESPN API response"""
    
    # Test with a recent date - yesterday
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    print(f"Testing with date: {yesterday}")
    
    # Test soccer EPL
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"
    params = {"dates": yesterday}
    
    print(f"\nURL: {url}")
    print(f"Params: {params}")
    print("-" * 80)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, params=params)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                events = data.get("events", [])
                print(f"\nTotal events found: {len(events)}")
                
                if not events:
                    print("No events found for this date!")
                    # Try a different date - let's try a few days ago
                    for i in range(1, 10):
                        test_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
                        print(f"\n\nTrying date: {test_date}")
                        response2 = await client.get(url, params={"dates": test_date})
                        if response2.status_code == 200:
                            data2 = response2.json()
                            events2 = data2.get("events", [])
                            print(f"Events found: {len(events2)}")
                            if events2:
                                # Show first event details
                                event = events2[0]
                                print(f"\nFirst event ID: {event.get('id')}")
                                print(f"First event name: {event.get('name')}")
                                status = event.get("status", {})
                                print(f"Full status object: {json.dumps(status, indent=2)}")
                                status_type = status.get("type")
                                print(f"\nstatus_type: {status_type}")
                                print(f"status_type type: {type(status_type)}")
                                if isinstance(status_type, dict):
                                    print(f"status_type keys: {status_type.keys()}")
                                    print(f"completed: {status_type.get('completed')}")
                                    print(f"name: {status_type.get('name')}")
                                break
                    return
                
                # Show first 3 events
                for i, event in enumerate(events[:3]):
                    print(f"\n{'='*60}")
                    print(f"Event {i+1}:")
                    print(f"  ID: {event.get('id')}")
                    print(f"  Name: {event.get('name')}")
                    
                    # Status
                    status = event.get("status", {})
                    print(f"  Status: {json.dumps(status, indent=4)}")
                    
                    status_type = status.get("type")
                    print(f"  status_type: {status_type}")
                    print(f"  status_type type: {type(status_type)}")
                    
                    if isinstance(status_type, dict):
                        print(f"  Keys in status_type: {status_type.keys()}")
                        print(f"  completed: {status_type.get('completed')}")
                        print(f"  name: {status_type.get('name')}")
                    elif isinstance(status_type, str):
                        print(f"  Status string: {status_type}")
                        print(f"  Contains 'final': {'final' in status_type.lower()}")
                    
                    # Competitors
                    competitions = event.get("competitions", [])
                    if competitions:
                        competitors = competitions[0].get("competitors", [])
                        for comp in competitors:
                            team = comp.get("team", {})
                            print(f"  {comp.get('homeAway')} - {team.get('displayName')}: Score = {comp.get('score')}")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_espn())
