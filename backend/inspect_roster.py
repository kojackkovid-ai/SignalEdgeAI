import asyncio
import httpx
import json

async def inspect_espn_roster():
    # NBA path
    base_url = "http://site.api.espn.com/apis/site/v2/sports/basketball/nba"
    
    async with httpx.AsyncClient() as client:
        # Get a team ID first (e.g., from scoreboard)
        scoreboard_url = f"{base_url}/scoreboard"
        resp = await client.get(scoreboard_url)
        data = resp.json()
        
        if not data.get("events"):
            print("No events found")
            return
            
        team_id = data["events"][0]["competitions"][0]["competitors"][0]["team"]["id"]
        print(f"Inspecting roster for team ID: {team_id}")
        
        # Get roster with stats enabled
        roster_url = f"{base_url}/teams/{team_id}/roster?enable=statistics"
        print(f"Fetching: {roster_url}")
        resp = await client.get(roster_url)
        roster_data = resp.json()
        
        if "athletes" in roster_data and len(roster_data["athletes"]) > 0:
            # Find a player with stats
            for athlete in roster_data["athletes"]:
                 # Check keys
                 if "stats" in athlete or "statistics" in athlete:
                     print("Found stats in athlete object!")
                     print(json.dumps(athlete, indent=2))
                     break
            else:
                 print("No stats found in any athlete object")
                 print(json.dumps(roster_data["athletes"][0], indent=2))
        else:
            print("No athletes found in roster")

if __name__ == "__main__":
    asyncio.run(inspect_espn_roster())