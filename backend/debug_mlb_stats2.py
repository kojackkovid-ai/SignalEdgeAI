"""Debug MLB athlete stats API response - get categories"""
import asyncio
import httpx
import json

async def test():
    player_id = "32655"
    url = f"https://site.web.api.espn.com/apis/common/v3/sports/baseball/mlb/athletes/{player_id}/stats"
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url)
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"Keys: {data.keys()}")
            
            # Get categories
            categories = data.get("categories", [])
            print(f"\nCategories: {json.dumps(categories, indent=2)}")

asyncio.run(test())
