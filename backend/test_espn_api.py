"""
Test script to diagnose ESPN API issues
"""
import asyncio
import httpx
from datetime import datetime, timedelta

async def test_espn_api():
    """Test ESPN API for different sports and dates"""
    client = httpx.AsyncClient(timeout=10.0)
    
    sports = [
        ("basketball/nba", "NBA"),
        ("hockey/nhl", "NHL"),
        ("football/nfl", "NFL"),
        ("baseball/mlb", "MLB"),
        ("soccer/eng.1", "EPL"),
    ]
    
    # Test different date ranges
    test_dates = [
        datetime.now() - timedelta(days=1),  # Yesterday
        datetime.now() - timedelta(days=7),  # Last week
        datetime.now() - timedelta(days=30),  # Last month
        datetime(2025, 2, 1),  # Specific date in past
        datetime(2025, 1, 15),  # Another specific date
    ]
    
    for sport_path, sport_name in sports:
        print(f"\n{'='*60}")
        print(f"Testing {sport_name} ({sport_path})")
        print(f"{'='*60}")
        
        for test_date in test_dates:
            date_str = test_date.strftime("%Y%m%d")
            url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard"
            
            try:
                response = await client.get(url, params={"dates": date_str})
                print(f"\nDate: {date_str} (Status: {response.status_code})")
                
                if response.status_code == 200:
                    data = response.json()
                    events = data.get("events", [])
                    print(f"  Events found: {len(events)}")
                    
                    if events:
                        # Show first event details
                        event = events[0]
                        status = event.get("status", {})
                        status_type = status.get("type", {})
                        
                        print(f"  First event: {event.get('name', 'N/A')}")
                        print(f"  Status: {status_type.get('name', 'N/A')}")
                        print(f"  Completed: {status_type.get('completed', 'N/A')}")
                        
                        # Check competitors
                        competitions = event.get("competitions", [])
                        if competitions:
                            competitors = competitions[0].get("competitors", [])
                            if competitors:
                                for comp in competitors:
                                    team = comp.get("team", {})
                                    score = comp.get("score", "N/A")
                                    print(f"    {team.get('displayName', 'N/A')}: {score}")
                    
                else:
                    print(f"  Error: {response.text[:200]}")
                    
            except Exception as e:
                print(f"  Exception: {e}")
    
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_espn_api())
