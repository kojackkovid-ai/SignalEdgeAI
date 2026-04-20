import asyncio
import httpx
import json

async def test_squad():
    async with httpx.AsyncClient(timeout=15) as client:
        # Get EPL teams
        print("=== FETCHING EPL SCOREBOARD ===")
        url = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?dates=20260426"
        resp = await client.get(url)
        data = resp.json()
        
        if 'events' in data and data['events']:
            event = data['events'][0]
            print(f"Game: {event['name']}")
            
            # Get team IDs
            home_id = event['competitions'][0]['competitors'][0]['id']
            away_id = event['competitions'][0]['competitors'][1]['id']
            print(f"Home team ID: {home_id}")
            print(f"Away team ID: {away_id}")
            
            # Test squad endpoint
            print(f"\n=== FETCHING SQUAD FOR HOME TEAM {home_id} ===")
            squad_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/teams/{home_id}/squad"
            squad_resp = await client.get(squad_url)
            print(f"Status: {squad_resp.status_code}")
            squad_data = squad_resp.json()
            
            if 'squad' in squad_data:
                print(f"Squad count: {len(squad_data['squad'])}")
                print(f"Squad structure:\n{json.dumps(squad_data['squad'][:1], indent=2)}")
            else:
                print(f"Response keys: {list(squad_data.keys())}")
                print(f"Full response:\n{json.dumps(squad_data, indent=2)}")
        
asyncio.run(test_squad())
