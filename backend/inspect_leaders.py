import asyncio
import httpx
import json

async def inspect_summary_leaders():
    # NBA path
    base_url = "http://site.api.espn.com/apis/site/v2/sports/basketball/nba"
    
    async with httpx.AsyncClient() as client:
        # Get a game ID first
        scoreboard_url = f"{base_url}/scoreboard"
        resp = await client.get(scoreboard_url)
        data = resp.json()
        
        if not data.get("events"):
            print("No events found")
            return
            
        event_id = data["events"][0]["id"]
        print(f"Inspecting summary for event: {event_id}")
        
        # Get summary
        summary_url = f"{base_url}/summary?event={event_id}"
        resp = await client.get(summary_url)
        summary_data = resp.json()
        
        if "leaders" in summary_data:
            print("Found leaders in summary:")
            for leader in summary_data["leaders"]:
                print(f"Category: {leader.get('name')}")
                if "leaders" in leader and len(leader["leaders"]) > 0:
                    for player in leader["leaders"]:
                        print(f"  Player: {player.get('athlete', {}).get('displayName')}")
                        print(f"  Value: {player.get('value')}")
                        print(f"  Team: {player.get('team', {}).get('displayName')}")
                        break
        else:
            print("No leaders found in summary")

if __name__ == "__main__":
    asyncio.run(inspect_summary_leaders())