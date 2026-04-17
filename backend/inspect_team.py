import asyncio
import httpx
import json

async def inspect_team_details():
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
        print(f"Inspecting team details for ID: {team_id}")
        
        # Get team details with roster enabled
        team_url = f"{base_url}/teams/{team_id}?enable=roster"
        resp = await client.get(team_url)
        team_data = resp.json()
        
        if "team" in team_data:
            team = team_data["team"]
            if "nextEvent" in team and len(team["nextEvent"]) > 0:
                 print("Found next event")
            
            # Check if roster has stats in this view
            # Note: The structure might be different
            # It seems the previous roster call was actually just returning the list of athletes
            pass
            
        # Let's try to find stats in the athlete object from the team endpoint
        # The previous output showed links to stats.
        
        # Another option: specific player stats endpoint
        # http://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster
        
        # Let's try the summary endpoint for a game
        event_id = data["events"][0]["id"]
        summary_url = f"{base_url}/summary?event={event_id}"
        print(f"Inspecting summary for event: {event_id}")
        resp = await client.get(summary_url)
        summary_data = resp.json()
        
        # Check for boxscore or leaders
        if "boxscore" in summary_data:
            print("Found boxscore")
        if "leaders" in summary_data:
            print("Found leaders")
            
if __name__ == "__main__":
    asyncio.run(inspect_team_details())