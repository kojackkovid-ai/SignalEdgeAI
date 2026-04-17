"""
Debug script to inspect the actual structure of ESPN soccer squad API response
"""
import asyncio
import httpx
import json

async def debug_soccer_squad():
    async with httpx.AsyncClient() as client:
        # Test with Manchester City (team ID 380)
        url = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/teams/380/squad"
        print(f"Fetching: {url}")
        
        try:
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            data = response.json()
            
            # Print all top-level keys
            print(f"\nTop-level keys: {list(data.keys())}")
            
            # Check if 'squad' exists
            if 'squad' in data:
                squad = data['squad']
                print(f"\n'squad' type: {type(squad)}")
                
                if isinstance(squad, list):
                    print(f"Squad is a list with {len(squad)} items")
                    if squad:
                        print(f"\nFirst item type: {type(squad[0])}")
                        print(f"First item keys: {list(squad[0].keys()) if isinstance(squad[0], dict) else 'Not a dict'}")
                        print(f"\nFirst player sample: {json.dumps(squad[0], indent=2)}")
                        
                        # Check position structure
                        if isinstance(squad[0], dict) and 'position' in squad[0]:
                            pos = squad[0]['position']
                            print(f"\nPosition type: {type(pos)}")
                            print(f"Position value: {pos}")
                
                elif isinstance(squad, dict):
                    print(f"Squad is a dict with keys: {list(squad.keys())}")
                    if 'athletes' in squad:
                        athletes = squad['athletes']
                        print(f"\n'athletes' type: {type(athletes)}")
                        if isinstance(athletes, list):
                            print(f"Athletes list has {len(athletes)} items")
                            if athletes:
                                print(f"First athlete: {json.dumps(athletes[0], indent=2)}")
            
            # Check if 'athletes' exists at top level
            if 'athletes' in data:
                athletes = data['athletes']
                print(f"\nTop-level 'athletes' type: {type(athletes)}")
                if isinstance(athletes, list):
                    print(f"Athletes list has {len(athletes)} items")
            
            # Check if 'team' exists
            if 'team' in data:
                team = data['team']
                print(f"\n'team' type: {type(team)}")
                if isinstance(team, dict):
                    print(f"Team keys: {list(team.keys())}")
                    if 'squad' in team:
                        print("Team has 'squad' key")
                    if 'athletes' in team:
                        print("Team has 'athletes' key")
            
            # Save full response for inspection
            with open("soccer_squad_full.json", "w") as f:
                json.dump(data, f, indent=2)
            print("\nSaved full response to soccer_squad_full.json")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_soccer_squad())
