import asyncio
import httpx
from datetime import datetime

async def simple_test():
    """Test ESPN API without any ML dependencies"""
    client = httpx.AsyncClient(timeout=10.0)
    
    today = datetime.now().strftime('%Y%m%d')
    url = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=' + today
    
    print('Fetching:', url)
    resp = await client.get(url)
    data = resp.json()
    events = data.get('events', [])
    print('Events from ESPN:', len(events))
    
    # Process just like the service does
    games = []
    now = datetime.utcnow()  # FIX: Use UTC to match timezone-aware game dates
    
    for event in events:
        competition = event.get("competitions", [{}])[0]
        competitors = competition.get("competitors", [])
        
        home_team = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away_team = next((c for c in competitors if c.get("homeAway") == "away"), None)
        
        if not home_team or not away_team:
            continue
            
        status = event.get("status", {}).get("type", {}).get("name", "")
        completed = event.get("status", {}).get("type", {}).get("completed", False)
        
        # Skip completed games
        status_lower = status.lower() if status else ''
        if completed or 'final' in status_lower or 'completed' in status_lower:
            print(f"Skipping {event.get('id')} - completed")
            continue
        if 'postpon' in status_lower or 'cancel' in status_lower or 'delay' in status_lower:
            print(f"Skipping {event.get('id')} - postponed/canceled")
            continue
            
        # Check game time
        game_date = event.get("date", "")
        if game_date:
            try:
                if 'T' in game_date:
                    # Parse the ISO format date and convert to UTC for comparison
                    game_dt = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
                    # Convert to naive datetime for comparison with now (which is also naive)
                    game_dt_utc = game_dt.replace(tzinfo=None)
                else:
                    game_dt = datetime.fromisoformat(game_date)
                    game_dt_utc = game_dt
                
                time_diff = (now - game_dt_utc).total_seconds()
                if time_diff > 300:
                    print(f"Skipping {event.get('id')} - already started")
                    continue
            except Exception as e:
                print(f"Date parse error for {event.get('id')}: {e}")
                continue
        
        # Extract team records
        home_record = home_team.get("records", [])
        away_record = away_team.get("records", [])
        
        home_record_str = ""
        away_record_str = ""
        if home_record and len(home_record) > 0:
            home_record_str = home_record[0].get("summary", "")
        if away_record and len(away_record) > 0:
            away_record_str = away_record[0].get("summary", "")
        
        home_wins = 0
        home_losses = 0
        away_wins = 0
        away_losses = 0
        
        # Parse home record
        if home_record:
            for rec in home_record:
                rec_summary = rec.get("summary", "")
                if rec_summary and "-" in rec_summary:
                    parts = rec_summary.split("-")
                    try:
                        if len(parts) >= 2:
                            if len(parts) == 3:
                                home_wins = int(parts[0])
                                home_losses = int(parts[2])
                            else:
                                home_wins = int(parts[0])
                                home_losses = int(parts[1])
                            break
                    except:
                        pass
        
        # Parse away record
        if away_record:
            for rec in away_record:
                rec_summary = rec.get("summary", "")
                if rec_summary and "-" in rec_summary:
                    parts = rec_summary.split("-")
                    try:
                        if len(parts) >= 2:
                            if len(parts) == 3:
                                away_wins = int(parts[0])
                                away_losses = int(parts[2])
                            else:
                                away_wins = int(parts[0])
                                away_losses = int(parts[1])
                            break
                    except:
                        pass
        
        game = {
            "id": event["id"],
            "date": event["date"],
            "status": status,
            "completed": completed,
            "sport_key": "basketball_nba",
            "home_team": {
                "id": home_team["team"]["id"],
                "name": home_team["team"]["displayName"],
                "abbreviation": home_team["team"].get("abbreviation", ""),
                "record": home_record_str,
                "wins": home_wins,
                "losses": home_losses
            },
            "away_team": {
                "id": away_team["team"]["id"],
                "name": away_team["team"]["displayName"],
                "abbreviation": away_team["team"].get("abbreviation", ""),
                "record": away_record_str,
                "wins": away_wins,
                "losses": away_losses
            }
        }
        games.append(game)
        print(f"Added game: {game['away_team']['name']} @ {game['home_team']['name']}")
    
    print(f'\nTotal games after processing: {len(games)}')
    await client.aclose()

asyncio.run(simple_test())
