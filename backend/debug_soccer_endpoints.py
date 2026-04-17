"""
Debug script to find working soccer endpoints
"""
import asyncio
import httpx
import json

async def test_endpoints():
    async with httpx.AsyncClient() as client:
        # Different endpoints to try
        endpoints = [
            "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/teams/380",
            "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/teams/380/roster",
            "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/teams/380/squad",
            "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/athletes",
            "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/summary?event=740868",
        ]
        
        for url in endpoints:
            print(f"\n{'='*80}")
            print(f"Testing: {url}")
            print('='*80)
            
            try:
                response = await client.get(url)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Top-level keys: {list(data.keys())}")
                    
                    # Check for athletes in various locations
                    if 'athletes' in data:
                        athletes = data['athletes']
                        print(f"Found 'athletes' at top level, type: {type(athletes)}")
                        if isinstance(athletes, list) and athletes:
                            print(f"  Count: {len(athletes)}")
                            print(f"  First item keys: {list(athletes[0].keys()) if isinstance(athletes[0], dict) else 'Not a dict'}")
                        elif isinstance(athletes, dict):
                            print(f"  Athletes is dict with keys: {list(athletes.keys())}")
                    
                    if 'team' in data and isinstance(data['team'], dict):
                        team = data['team']
                        print(f"\n'team' keys: {list(team.keys())}")
                        if 'athletes' in team:
                            print("  Team has 'athletes'")
                        if 'squad' in team:
                            print("  Team has 'squad'")
                        if 'roster' in team:
                            print("  Team has 'roster'")
                    
                    if 'squad' in data:
                        squad = data['squad']
                        print(f"\n'squad' type: {type(squad)}")
                        if isinstance(squad, list):
                            print(f"  Squad list count: {len(squad)}")
                        elif isinstance(squad, dict):
                            print(f"  Squad dict keys: {list(squad.keys())}")
                    
                    # Save successful responses
                    filename = url.split('/')[-1].split('?')[0] + "_response.json"
                    with open(filename, "w") as f:
                        json.dump(data, f, indent=2)
                    print(f"\nSaved to {filename}")
                else:
                    print(f"Error: {response.status_code}")
                    
            except Exception as e:
                print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
