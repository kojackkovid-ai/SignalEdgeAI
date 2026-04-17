import asyncio
import httpx
import json

async def debug_soccer_roster():
    async with httpx.AsyncClient() as client:
        # Test soccer squad endpoint
        url = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/teams/380/squad"
        print(f"Fetching: {url}")
        try:
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            data = response.json()
            
            # Print top-level keys
            print(f"Top-level keys: {list(data.keys())}")
            
            # Check for squad or athletes
            if "squad" in data:
                print(f"Squad type: {type(data['squad'])}")
                if isinstance(data['squad'], list):
                    print(f"Squad size: {len(data['squad'])}")
                    if data['squad']:
                        print(f"First player: {data['squad'][0]}")
                elif isinstance(data['squad'], dict):
                    print(f"Squad keys: {list(data['squad'].keys())}")
            
            if "athletes" in data:
                print(f"Athletes type: {type(data['athletes'])}")
                if isinstance(data['athletes'], list):
                    print(f"Athletes size: {len(data['athletes'])}")
            
            # Save full response for inspection
            with open("soccer_squad_debug.json", "w") as f:
                json.dump(data, f, indent=2)
            print("Saved full response to soccer_squad_debug.json")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_soccer_roster())
