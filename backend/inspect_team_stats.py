import asyncio
import httpx
import json

async def inspect_team_stats():
    # NBA path
    base_url = "http://site.api.espn.com/apis/site/v2/sports/basketball/nba"
    
    async with httpx.AsyncClient() as client:
        # Get a team ID first
        scoreboard_url = f"{base_url}/scoreboard"
        resp = await client.get(scoreboard_url)
        data = resp.json()
        
        if not data.get("events"):
            print("No events found")
            return
            
        team_id = data["events"][0]["competitions"][0]["competitors"][0]["team"]["id"]
        print(f"Inspecting team stats for ID: {team_id}")
        
        # Get team stats
        stats_url = f"{base_url}/teams/{team_id}/statistics"
        resp = await client.get(stats_url)
        
        if resp.status_code == 200:
            stats_data = resp.json()
            print("Team stats response structure:")
            print(json.dumps(stats_data, indent=2))
        else:
            print(f"Team stats endpoint returned {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(inspect_team_stats())