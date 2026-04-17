#!/usr/bin/env python3
"""Test ESPN soccer squad endpoint directly."""

import asyncio
import httpx

async def test_soccer_squad():
    """Fetch actual soccer squad from ESPN to see the format."""
    
    # Find a current soccer team ID
    # Common soccer_usa_mls team IDs: 141, 142, 143, 144, 145, etc - these are DC United, Houston, LA, etc
    
    client = httpx.AsyncClient()
    
    for team_id in ["141", "142", "143"]:
        print(f"\n\n{'='*60}")
        print(f"Testing squad endpoint for team ID: {team_id}")
        print(f"{'='*60}\n")
        
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/usa.1/teams/{team_id}/squad"
        
        try:
            response = await client.get(url, timeout=10.0)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response keys: {list(data.keys())}")
                
                # Check for squad
                if 'squad' in data:
                    squad = data['squad']
                    print(f"\n✅ Found 'squad' key!")
                    print(f"Squad type: {type(squad).__name__}")
                    print(f"Squad length: {len(squad) if isinstance(squad, list) else 'N/A'}")
                    
                    if isinstance(squad, list) and len(squad) > 0:
                        print(f"\nFirst squad entry keys: {list(squad[0].keys())}")
                        print(f"First player: {squad[0].get('displayName', 'N/A')}")
                        print(f"First player position: {squad[0].get('position', 'N/A')}")
                elif 'athletes' in data:
                    print(f"\n✅ Found 'athletes' key instead")
                else:
                    print(f"\n❌ Neither 'squad' nor 'athletes' found!")
                    print(f"Available keys: {list(data.keys())}")
                    
                break  # Success, exit loop
                
            else:
                print(f"❌ Status {response.status_code}, trying next team...")
                
        except Exception as e:
            print(f"Error: {e}")
    
    await client.aclose()

if __name__ == '__main__':
    asyncio.run(test_soccer_squad())
