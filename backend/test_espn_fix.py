import asyncio
import httpx
import json
from datetime import datetime, timedelta

async def test_espn_api():
    """Test the ESPN API to see what status values are being returned"""
    
    # Test soccer EPL - yesterday's games
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"
    params = {"dates": yesterday}
    
    print(f"Testing ESPN API for soccer_epl on {yesterday}")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print("-" * 80)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            events = data.get("events", [])
            print(f"\nTotal events found: {len(events)}")
            
            for i, event in enumerate(events[:5]):  # Check first 5 events
                print(f"\n--- Event {i+1} ---")
                print(f"ID: {event.get('id')}")
                print(f"Name: {event.get('name')}")
                
                status_type = event.get("status", {}).get("type", {})
                print(f"Status Type: {json.dumps(status_type, indent=2)}")
                
                # Check the completed field
                is_completed = status_type.get("completed", False)
                status_name = status_type.get("name", "UNKNOWN")
                
                print(f"Status Name: {status_name}")
                print(f"Is Completed (from 'completed' field): {is_completed}")
                
                # Check if our fix would catch this
                if is_completed:
                    print("✓ Would be INCLUDED (completed=True)")
                else:
                    print("✗ Would be SKIPPED (completed=False)")
                
                # Show competitors if available
                competitions = event.get("competitions", [])
                if competitions:
                    competitors = competitions[0].get("competitors", [])
                    for comp in competitors:
                        team = comp.get("team", {})
                        print(f"  Team: {team.get('displayName')} - Score: {comp.get('score')}")
                
                print("-" * 40)

if __name__ == "__main__":
    asyncio.run(test_espn_api())
