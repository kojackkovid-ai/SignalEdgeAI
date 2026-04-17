import asyncio
import httpx
import json

async def fetch_athlete_data():
    sport_path = "basketball/nba"
    athlete_id = "1966" # LeBron James
    
    stats_url = f"https://site.web.api.espn.com/apis/common/v3/sports/{sport_path}/athletes/{athlete_id}/stats"
    gamelog_url = f"https://site.web.api.espn.com/apis/common/v3/sports/{sport_path}/athletes/{athlete_id}/gamelog"
    
    with open("api_debug_output.txt", "w") as f:
        async with httpx.AsyncClient() as client:
            f.write(f"Fetching stats from: {stats_url}\n")
            stats_resp = await client.get(stats_url)
            if stats_resp.status_code == 200:
                data = stats_resp.json()
                categories = data.get("categories", [])
                f.write("\nStats Categories found:\n")
                for cat in categories:
                    f.write(f"- {cat.get('name')} (Display: {cat.get('displayName')})\n")
            else:
                f.write(f"Error fetching stats: {stats_resp.status_code}\n")
                
            f.write(f"\nFetching gamelog from: {gamelog_url}\n")
            log_resp = await client.get(gamelog_url)
            if log_resp.status_code == 200:
                data = log_resp.json()
                f.write(f"Gamelog keys: {list(data.keys())}\n")
                f.write(f"Display Names: {data.get('displayNames')}\n")
                f.write(f"Names: {data.get('names')}\n")
                
                season_types = data.get("seasonTypes", [])
                for st in season_types:
                    f.write(f"Season Type: {st.get('displayName')}\n")
                    categories = st.get("categories", [])
                    for cat in categories:
                        f.write(f"  Category: {cat.get('name')}\n")
                        events = cat.get("events", [])
                        f.write(f"  Events count: {len(events)}\n")
                        if events:
                            # Try to find date
                            f.write(f"  First event date: {events[0].get('gameDate')}\n")
                            f.write(f"  First event stats: {events[0].get('stats')}\n")
            else:
                f.write(f"Error fetching gamelog: {log_resp.status_code}\n")

if __name__ == "__main__":
    asyncio.run(fetch_athlete_data())