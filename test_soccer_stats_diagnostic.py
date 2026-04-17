"""
Diagnostic script to test soccer stats fetching from ESPN API
"""
import asyncio
import httpx
import json

async def test_soccer_athlete_stats():
    """Test if ESPN soccer stats endpoint works"""
    
    # Test with a real MLS player ID if we can find one
    # For now, let's test the endpoint structure
    
    async with httpx.AsyncClient(timeout=10) as client:
        # Try different methods to get athlete stats
        
        # Method 1: Direct athlete stats endpoint
        print("=" * 80)
        print("METHOD 1: Direct athlete stats endpoint")
        print("=" * 80)
        
        athlete_ids = [
            "3087883",  # Common MLS player ID
            "3121518",
            "3056916",
        ]
        
        for athlete_id in athlete_ids:
            url = f"https://site.web.api.espn.com/apis/common/v3/sports/soccer/usa.1/athletes/{athlete_id}/stats"
            print(f"\nTesting: {url}")
            try:
                resp = await client.get(url)
                print(f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    print(f"Response keys: {list(data.keys())}")
                    if "categories" in data:
                        print(f"Categories count: {len(data['categories'])}")
                        for cat in data.get("categories", [])[:2]:
                            print(f"  - {cat.get('name')}")
                    else:
                        print("No categories in response")
                    break
            except Exception as e:
                print(f"Error: {e}")
        
        # Method 2: Scoreboard to get athlete IDs
        print("\n" + "=" * 80)
        print("METHOD 2: Get real athlete IDs from scoreboard")
        print("=" * 80)
        
        # Get a recent MLS game
        url = "https://site.web.api.espn.com/apis/common/v3/sports/soccer/usa.1/scoreboard"
        print(f"\nFetching: {url}")
        try:
            resp = await client.get(url)
            data = resp.json()
            
            if "events" in data and len(data["events"]) > 0:
                event = data["events"][0]
                print(f"Latest game: {event.get('name')}")
                print(f"Event ID: {event.get('id')}")
                
                # Get competitors
                competitors = event.get("competitions", [{}])[0].get("competitors", [])
                print(f"Competitors: {len(competitors)}")
                
                for comp in competitors:
                    team = comp.get("team", {})
                    print(f"\n  Team: {team.get('displayName')}")
                    
                    competitors_data = comp.get("competitors", [])
                    if competitors_data:
                        print(f"  Competitors count: {len(competitors_data)}")
                        for athlete in competitors_data[:3]:
                            athlete_id = athlete.get("id")
                            athlete_name = athlete.get("displayName")
                            print(f"    - {athlete_name} (ID: {athlete_id})")
                            
                            # Try to fetch stats for this athlete
                            stats_url = f"https://site.web.api.espn.com/apis/common/v3/sports/soccer/usa.1/athletes/{athlete_id}/stats"
                            print(f"      Testing stats endpoint...")
                            try:
                                stats_resp = await client.get(stats_url)
                                print(f"      Stats status: {stats_resp.status_code}")
                                if stats_resp.status_code == 200:
                                    stats_data = stats_resp.json()
                                    if "categories" in stats_data and len(stats_data["categories"]) > 0:
                                        print(f"      ✓ Got stats with {len(stats_data['categories'])} categories")
                                        cat = stats_data["categories"][0]
                                        print(f"        Sample: {cat.get('name')} - {len(cat.get('statistics', []))} stat entries")
                                    else:
                                        print(f"      ✗ No categories in stats response")
                            except Exception as e:
                                print(f"      Error: {type(e).__name__}")
        
        except Exception as e:
            print(f"Error: {e}")
        
        # Method 3: Check if stats endpoint even exists for soccer
        print("\n" + "=" * 80)
        print("METHOD 3: Test endpoint existence for different sports")
        print("=" * 80)
        
        test_endpoints = [
            ("Baseball", "http://site.web.api.espn.com/apis/common/v3/sports/baseball/mlb/scoreboard"),
            ("Soccer", "http://site.web.api.espn.com/apis/common/v3/sports/soccer/usa.1/scoreboard"),
            ("Basketball", "http://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/scoreboard"),
        ]
        
        for sport_name, endpoint in test_endpoints:
            try:
                resp = await client.get(endpoint)
                print(f"{sport_name}: {resp.status_code}")
            except Exception as e:
                print(f"{sport_name}: ERROR - {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_soccer_athlete_stats())
