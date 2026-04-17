"""Quick MLB test without ML service"""
import asyncio
import httpx
from datetime import datetime, timedelta

async def test():
    print("Testing ESPN API for all sports...")
    
    sports = [
        ("basketball_nba", "basketball/nba"),
        ("icehockey_nhl", "hockey/nhl"),
        ("baseball_mlb", "baseball/mlb"),
    ]
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        for sport_key, espn_path in sports:
            print(f"\n{sport_key}:")
            # Try today's date
            today = datetime.now().strftime("%Y%m%d")
            url = f"https://site.api.espn.com/apis/site/v2/sports/{espn_path}/scoreboard"
            resp = await client.get(url, params={"dates": today})
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                events = data.get("events", [])
                print(f"  Events: {len(events)}")
                if events:
                    # Show sample game
                    event = events[0]
                    print(f"  Sample: {event.get('id')}")

asyncio.run(test())
