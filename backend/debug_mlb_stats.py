"""Debug MLB athlete stats API response"""
import asyncio
import httpx

async def test():
    # Test player stats API
    # Using Byron Buxton (ID: 32655) as test
    player_id = "32655"
    url = f"https://site.web.api.espn.com/apis/common/v3/sports/baseball/mlb/athletes/{player_id}/stats"
    
    print(f"Fetching: {url}")
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"\nResponse keys: {data.keys()}")
            print(f"\nFull response:\n{json.dumps(data, indent=2)[:3000]}")

import json
asyncio.run(test())
