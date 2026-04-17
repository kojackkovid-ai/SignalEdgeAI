import httpx
import asyncio
import json

async def debug_athlete_stats():
    team_id = "8" # Pistons
    
    async with httpx.AsyncClient() as client:
        # 1. Get Roster to get an ID
        print("Fetching Roster...")
        resp = await client.get(f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster")
        data = resp.json()
        athletes = data.get("athletes", [])
        
        target_athlete = next((a for a in athletes if "Cunningham" in a.get("displayName", "")), athletes[0])
        athlete_id = target_athlete.get("id")
        print(f"Testing with Athlete: {target_athlete.get('displayName')} (ID: {athlete_id})")
        
        # 2. Fetch Stats
        # Try the endpoint found in search
        url = f"https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{athlete_id}/stats"
        print(f"\nFetching Stats from: {url}")
        
        resp = await client.get(url)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            stats_data = resp.json()
            # Inspect structure
            # Usually has categories (Regular Season, etc.)
            categories = stats_data.get("categories", [])
            for cat in categories:
                print(f"Category: {cat.get('name')}")
                # Look for "Regular Season"
                if cat.get("name") == "statistics":
                     for stat_type in cat.get("statistics", []):
                         print(f"  Type: {stat_type.get('name')}")
                         if stat_type.get("name") == "regularSeasonStats":
                             season_stats = stat_type.get("stats", [])
                             print(f"  Found {len(season_stats)} stat entries")
                             if season_stats:
                                 print(f"  Latest Season: {season_stats[-1].get('season', {}).get('year')}")
                                 print(f"  Stats: {season_stats[-1].get('stats')}") # Usually a list of values
                                 # We need to know what the values mean (labels)
                                 print(f"  Labels: {stat_type.get('names')}") # or 'descriptions'
                                 
        # 3. Try Team Stats Bulk Endpoint (Guessing)
        url_team = f"https://site.web.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/statistics" 
        print(f"\nTesting Team Stats: {url_team}")
        resp = await client.get(url_team)
        print(f"Status: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(debug_athlete_stats())
