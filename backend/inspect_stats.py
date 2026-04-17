import asyncio
import httpx
import json

async def inspect_statistics():
    # NBA path
    base_url = "http://site.api.espn.com/apis/site/v2/sports/basketball/nba"
    
    async with httpx.AsyncClient() as client:
        # Try statistics endpoint
        stats_url = f"{base_url}/statistics"
        resp = await client.get(stats_url)
        
        if resp.status_code == 200:
            stats_data = resp.json()
            print("Statistics endpoint response structure:")
            print(json.dumps(stats_data, indent=2))
        else:
            print(f"Statistics endpoint returned {resp.status_code}")
        
        # Try leaders endpoint
        leaders_url = f"{base_url}/leaders"
        resp = await client.get(leaders_url)
        
        if resp.status_code == 200:
            leaders_data = resp.json()
            print("\nLeaders endpoint response structure:")
            print(json.dumps(leaders_data, indent=2))
        else:
            print(f"Leaders endpoint returned {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(inspect_statistics())