import asyncio
from datetime import datetime
import httpx

async def debug_fetch():
    client = httpx.AsyncClient(timeout=10.0)
    today = datetime.now().strftime('%Y%m%d')
    url = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=' + today
    
    resp = await client.get(url)
    data = resp.json()
    events = data.get('events', [])
    
    print('Total events from ESPN:', len(events))
    
    # Check status of each event
    for event in events:
        competition = event.get('competitions', [{}])[0]
        status = competition.get('status', {}).get('type', {}).get('name', 'UNKNOWN')
        completed = competition.get('status', {}).get('completed', False)
        date = event.get('date', '')
        
        # Check if game has started (more than 5 min ago)
        game_started = False
        if date:
            try:
                if 'T' in date:
                    game_dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                else:
                    game_dt = datetime.fromisoformat(date)
                now = datetime.now(game_dt.tzinfo) if game_dt.tzinfo else datetime.now()
                time_diff = (now - game_dt).total_seconds()
                game_started = time_diff > 300
            except:
                pass
        
        print(f'  Event {event.get("id")}: status={status}, completed={completed}, game_started={game_started}')
        
        # This is what the filtering code does
        status_lower = status.lower() if status else ''
        if completed or 'final' in status_lower or 'completed' in status_lower:
            print(f'    -> FILTERED: completed/final')
        elif 'postpon' in status_lower or 'cancel' in status_lower or 'delay' in status_lower:
            print(f'    -> FILTERED: postpon/cancel/delay')
        elif game_started:
            print(f'    -> FILTERED: game already started')
        else:
            print(f'    -> KEPT')
    
    await client.aclose()

asyncio.run(debug_fetch())
