#!/usr/bin/env python3
"""Diagnostic test - trace exactly what's returned for soccer props."""

import asyncio
import aiohttp
import json

async def test_soccer_api():
    """Call the exact endpoint the frontend uses and show full response."""
    
    # These are the exact params the frontend sends
    sport_key = "soccer_usa_mls"
    event_id = "761502"  # Your example event
    
    print("="*80)
    print("SOCCER PROPS DIAGNOSTIC TEST")
    print("="*80)
    print(f"\nTesting: /api/predictions/game/{sport_key}/{event_id}/full")
    print(f"Sport: {sport_key}")
    print(f"Event ID: {event_id}\n")
    
    # Create a fake auth token
    token = "test_token_12345"
    
    url = f"http://127.0.0.1:8000/api/predictions/game/{sport_key}/{event_id}/full"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"Calling API... (timeout: 180 seconds)")
            async with session.get(url, headers=headers, timeout=180) as response:
                print(f"\n✓ Status Code: {response.status}")
                
                data = await response.json()
                
                # Show structure
                print(f"\nResponse Keys: {list(data.keys())}")
                
                # Show props_summary
                if 'props_summary' in data:
                    summary = data['props_summary']
                    print(f"\n📊 Props Summary:")
                    for key, val in summary.items():
                        print(f"  {key}: {val}")
                
                # Show array sizes
                print(f"\n📈 Array Sizes:")
                print(f"  goals: {len(data.get('goals', []))}")
                print(f"  assists: {len(data.get('assists', []))}")
                print(f"  anytime_goal: {len(data.get('anytime_goal', []))}")
                print(f"  team_props: {len(data.get('team_props', []))}")
                print(f"  other_props: {len(data.get('other_props', []))}")
                
                # Check first prop details
                all_props = data.get('goals', []) + data.get('assists', []) + data.get('team_props', [])
                
                if all_props:
                    print(f"\n✅ PROPS FOUND: {len(all_props)} total")
                    first = all_props[0]
                    
                    print(f"\n🎯 First Prop Details:")
                    print(f"  player: {first.get('player', '❌ MISSING')}")
                    print(f"  market_key: {first.get('market_key', '❌ MISSING')}")
                    print(f"  prediction: {first.get('prediction', '❌ MISSING')}")
                    print(f"  confidence: {first.get('confidence', '❌ MISSING')}")
                    print(f"  season_avg: {first.get('season_avg', '❌ MISSING')}")
                    print(f"  recent_10_avg: {first.get('recent_10_avg', '❌ MISSING')}")
                    print(f"  home_team_stats: {'✓ PRESENT' if first.get('home_team_stats') else '❌ MISSING'}")
                    print(f"  away_team_stats: {'✓ PRESENT' if first.get('away_team_stats') else '❌ MISSING'}")
                    
                    # Show full first prop
                    print(f"\n📋 Full First Prop JSON:")
                    print(json.dumps(first, indent=2, default=str)[:1000])
                else:
                    print(f"\n❌ NO PROPS FOUND - All arrays empty!")
                    print(f"Full response (truncated):")
                    print(json.dumps(data, indent=2, default=str)[:2000])
                    
    except asyncio.TimeoutError:
        print("❌ API call timed out (180 seconds)")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_soccer_api())
