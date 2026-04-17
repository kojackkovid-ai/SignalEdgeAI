"""
Debug script to understand ESPN API response structure
"""
import asyncio
import httpx
import json
from datetime import datetime, timedelta

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"

# Test with soccer
async def test_espn_api():
    async with httpx.AsyncClient() as client:
        # Test La Liga (soccer/esp.1)
        sport_path = "soccer/esp.1"
        
        # Get yesterday's date
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime("%Y%m%d")
        
        url = f"{BASE_URL}/{sport_path}/scoreboard"
        params = {"dates": date_str}
        
        print(f"Fetching: {url} with params {params}")
        
        try:
            response = await client.get(url, params=params)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Save full response for inspection
                with open("espn_response_debug.json", "w") as f:
                    json.dump(data, f, indent=2)
                print("Saved full response to espn_response_debug.json")
                
                # Analyze structure
                events = data.get("events", [])
                print(f"\nTotal events: {len(events)}")
                
                completed_games = 0
                for i, event in enumerate(events[:5]):  # Check first 5
                    print(f"\n--- Event {i+1} ---")
                    print(f"ID: {event.get('id')}")
                    print(f"Name: {event.get('name')}")
                    
                    # Check status
                    status = event.get("status", {})
                    print(f"Status: {json.dumps(status, indent=2)}")
                    
                    # Check competitions
                    competitions = event.get("competitions", [])
                    print(f"Competitions count: {len(competitions)}")
                    
                    if competitions:
                        comp = competitions[0]
                        competitors = comp.get("competitors", [])
                        print(f"Competitors count: {len(competitors)}")
                        
                        for j, competitor in enumerate(competitors):
                            print(f"  Competitor {j+1}:")
                            print(f"    homeAway: {competitor.get('homeAway')}")
                            print(f"    winner: {competitor.get('winner')}")
                            print(f"    score: {competitor.get('score')}")
                            print(f"    team: {competitor.get('team', {}).get('displayName')}")
                    
                    # Check if completed
                    status_type = status.get("type", {})
                    status_name = status_type.get("name", "")
                    print(f"Status name: {status_name}")
                    
                    if status_name in ["STATUS_FINAL", "STATUS_COMPLETED"]:
                        completed_games += 1
                        print("  -> COMPLETED")
                    else:
                        print(f"  -> NOT COMPLETED (status: {status_name})")
                
                print(f"\nCompleted games found: {completed_games}")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_espn_api())
