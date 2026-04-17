"""Debug script to try alternative ESPN API endpoints for player stats"""
import asyncio
import httpx

async def try_alternative_endpoints():
    async with httpx.AsyncClient(timeout=15.0) as client:
        player_id = '4277848'  # Marvin Bagley III from roster
        
        endpoints = [
            # Option 1: Old v2 format
            f'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/athletes/{player_id}/statistics',
            # Option 2: Box score - has player stats
            f'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event=401610083',
            # Option 3: Leaderboard endpoint - might have player stats
            f'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/leaders',
            # Option 4: Player insight - might have stats
            f'https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{player_id}/projection',
        ]
        
        for url in endpoints:
            print(f'\n--- Trying ---')
            print(url[:80])
            try:
                response = await client.get(url)
                print(f'Status: {response.status_code}')
                if response.status_code == 200:
                    data = response.json()
                    print(f'Keys: {list(data.keys())[:10]}')
                    if 'categories' in data:
                        print(f'Categories found: {len(data.get("categories", []))}')
                    if 'players' in data:
                        print(f'Players found in response')
            except Exception as e:
                print(f'Error: {e}')

async def try_boxscore():
    """Try to get player stats from box score"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Get a recent game box score
        event_id = '401610083'
        url = f'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/boxscore?event={event_id}'
        
        print(f'\n\n=== BOXSCORE ===')
        print(url)
        
        response = await client.get(url)
        print(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'Top keys: {list(data.keys())}')
            
            # Check for players
            if 'players' in data:
                print(f'Players found: {len(data.get("players", []))}')
                
            # Check gamePackage
            if 'gamePackage' in data:
                gp = data['gamePackage']
                print(f'GamePackage keys: {list(gp.keys()) if isinstance(gp, dict) else "not dict"}')

if __name__ == '__main__':
    asyncio.run(try_alternative_endpoints())
    asyncio.run(try_boxscore())
