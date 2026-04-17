#!/usr/bin/env python3
"""
Test ESPN API to see if games are being returned
"""
import asyncio
import httpx
from datetime import datetime, timedelta

async def test_espn_games():
    async with httpx.AsyncClient() as client:
        # Test NBA games
        sport_key = "basketball_nba"
        espn_path = "basketball/nba"
        
        today = datetime.now()
        today_str = today.strftime("%Y%m%d")
        
        url = f"https://site.api.espn.com/apis/site/v2/sports/{espn_path}/scoreboard"
        params = {"dates": today_str}
        
        print(f"Fetching NBA games for {today_str}...")
        response = await client.get(url, params=params)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            events = data.get("events", [])
            print(f"Number of events: {len(events)}")
            
            if events:
                print("\nFirst game:")
                event = events[0]
                print(f"  ID: {event.get('id')}")
                print(f"  Name: {event.get('name')}")
                print(f"  Date: {event.get('date')}")
                print(f"  Status: {event.get('status', {}).get('type', {}).get('name')}")
                
                # Check competitions
                competitions = event.get("competitions", [])
                if competitions:
                    comp = competitions[0]
                    competitors = comp.get("competitors", [])
                    print(f"  Competitors: {len(competitors)}")
                    for c in competitors:
                        print(f"    - {c.get('team', {}).get('displayName')} ({c.get('homeAway')})")
            else:
                print("No events found for today, checking next few days...")
                # Check next 7 days
                for i in range(1, 8):
                    next_date = today + timedelta(days=i)
                    next_date_str = next_date.strftime("%Y%m%d")
                    params = {"dates": next_date_str}
                    
                    response = await client.get(url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        events = data.get("events", [])
                        if events:
                            print(f"Found {len(events)} games on {next_date_str}")
                            break
                else:
                    print("No games found in the next 7 days")
        else:
            print(f"Error: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_espn_games())
