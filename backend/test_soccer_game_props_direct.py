#!/usr/bin/env python3
"""Direct test of the full game props endpoint for soccer."""

import asyncio
import aiohttp
import json

async def test_game_props():
    """Test the /api/predictions/game/sport/event/full endpoint directly."""
    
    # Use the event_id from the frontend error
    sport_key = "soccer_usa_mls"
    event_id = "761502"
    
    # Create fake token for testing
    fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIifQ.test"
    
    url = f"http://127.0.0.1:8000/api/predictions/game/{sport_key}/{event_id}/full"
    
    print(f"\nTesting: {url}")
    print(f"Event ID: {event_id}")
    print(f"Sport: {sport_key}\n")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Add auth header
            headers = {"Authorization": f"Bearer {fake_token}"}
            
            async with session.get(url, headers=headers, timeout=180) as response:
                print(f"Status: {response.status}")
                data = await response.json()
                
                # Check structure
                print(f"\n📊 Response Structure:")
                print(f"  Keys: {list(data.keys())}")
                
                if 'props_summary' in data:
                    summary = data.get('props_summary', {})
                    print(f"\n📈 Props Summary:")
                    for key, val in summary.items():
                        print(f"  {key}: {val}")
                
                # Check individual arrays
                print(f"\n🎯 Array Sizes:")
                print(f"  goals: {len(data.get('goals', []))}")
                print(f"  assists: {len(data.get('assists', []))}")
                print(f"  anytime_goal: {len(data.get('anytime_goal', []))}")
                print(f"  team_props: {len(data.get('team_props', []))}")
                print(f"  other_props: {len(data.get('other_props', []))}")
                
                # Show sample if we have any
                all_props = data.get('goals', []) + data.get('assists', []) + data.get('team_props', [])
                if all_props:
                    print(f"\n✅ SAMPLE PROP FOUND:")
                    sample = all_props[0]
                    print(f"  Player: {sample.get('player', 'N/A')}")
                    print(f"  Market: {sample.get('market_key', 'N/A')}")
                    print(f"  Prediction: {sample.get('prediction', 'N/A')}")
                    print(f"  Confidence: {sample.get('confidence', 'N/A')}")
                    print(f"  Season Avg: {sample.get('season_avg', 'N/A')}")
                    print(f"  Recent 10: {sample.get('recent_10_avg', 'N/A')}")
                    print(f"  Is Locked: {sample.get('is_locked', 'N/A')}")
                else:
                    print(f"\n❌ NO PROPS FOUND - All arrays empty!")
                    print(f"\nFull Response (truncated):")
                    print(json.dumps(data, indent=2, default=str)[:1000])
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_game_props())
