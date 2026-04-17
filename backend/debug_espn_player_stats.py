"""
Debug script to see what ESPN API actually returns for player stats
"""
import asyncio
import httpx
import json

async def debug_espn_stats():
    """Debug what ESPN API returns for player stats"""
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Test NBA player - Luka Doncic
        player_id = '3944'
        url = f'https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{player_id}/stats'
        
        print(f"Testing NBA player stats API...")
        print(f"URL: {url}")
        
        response = await client.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse keys: {data.keys()}")
            
            categories = data.get('categories', [])
            print(f"\nNumber of categories: {len(categories)}")
            
            for cat in categories:
                cat_name = cat.get('name', 'unknown')
                labels = cat.get('labels', [])
                names = cat.get('names', [])
                stats = cat.get('statistics', [])
                
                print(f"\n{'='*60}")
                print(f"Category: {cat_name}")
                print(f"Labels: {labels}")
                print(f"Names: {names}")
                
                if stats and len(stats) > 0:
                    # Get the most recent season
                    latest = stats[0]
                    season = latest.get('season', {})
                    print(f"Season: {season}")
                    print(f"Stats array: {latest.get('stats', [])[:15]}")
                    
                    # Create a mapping
                    if labels and names and latest.get('stats'):
                        print(f"\nActual stat mapping:")
                        for i, (label, name) in enumerate(zip(labels, names)):
                            if i < len(latest.get('stats', [])):
                                value = latest['stats'][i]
                                print(f"  {name} ({label}): {value}")
        else:
            print(f"Error: {response.text}")

async def debug_roster():
    """Debug roster fetching"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Get Dallas Mavericks roster
        team_id = '6'  # Dallas Mavericks
        url = f'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster'
        
        print(f"\n\nTesting roster API...")
        print(f"URL: {url}")
        
        response = await client.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {data.keys()}")
            
            athletes = data.get('athletes', [])
            print(f"Number of athletes: {len(athletes)}")
            
            if athletes:
                # Check structure
                first = athletes[0] if isinstance(athletes[0], dict) else athletes[0].get('items', [{}])[0] if isinstance(athletes[0], dict) and 'items' in athletes[0] else {}
                print(f"\nFirst athlete structure: {first.keys()}")
                print(f"First athlete: {json.dumps(first, indent=2)[:500]}")

if __name__ == '__main__':
    asyncio.run(debug_espn_stats())
    asyncio.run(debug_roster())
