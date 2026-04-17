import httpx
import asyncio
import json

async def debug_soccer():
    async with httpx.AsyncClient() as client:
        # Try different soccer endpoints
        urls = [
            'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/teams/380/squad',
            'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/teams/380/roster',
            'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/teams/380',
        ]
        for url in urls:
            print(f'\n=== {url} ===')
            try:
                resp = await client.get(url)
                print(f'Status: {resp.status_code}')
                data = resp.json()
                print(f'Keys: {list(data.keys())}')
                
                if 'squad' in data:
                    squad = data['squad']
                    print(f'Squad type: {type(squad)}')
                    if isinstance(squad, list):
                        print(f'Squad length: {len(squad)}')
                        if squad:
                            print(f'First item keys: {list(squad[0].keys()) if isinstance(squad[0], dict) else "Not a dict"}')
                            print(f'First item: {json.dumps(squad[0], indent=2)[:500]}')
                    elif isinstance(squad, dict):
                        print(f'Squad dict keys: {list(squad.keys())}')
                
                if 'athletes' in data:
                    athletes = data['athletes']
                    print(f'Athletes type: {type(athletes)}')
                    if isinstance(athletes, list):
                        print(f'Athletes length: {len(athletes)}')
                
                if 'team' in data:
                    team = data['team']
                    print(f'Team keys: {list(team.keys())}')
                    if 'squad' in team:
                        print(f'Team has squad key')
                    if 'athletes' in team:
                        print(f'Team has athletes key')
                        
            except Exception as e:
                print(f'Error: {e}')
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_soccer())
