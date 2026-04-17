#!/usr/bin/env python3
import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.WARNING)

async def test():
    from app.services.espn_prediction_service import ESPNPredictionService
    service = ESPNPredictionService()
    
    sports = ['basketball_nba', 'americanfootball_nfl', 'baseball_mlb']
    today = datetime.utcnow()
    
    print(f'Checking upcoming games as of {today.strftime("%Y-%m-%d %H:%M UTC")}')
    print('=' * 70)
    
    for sport in sports:
        try:
            games = await asyncio.wait_for(service.get_upcoming_games(sport), timeout=5)
            print(f'{sport}: Found {len(games)} games')
            if games:
                g = games[0]
                print(f'  Sample: {g.get("away_team", {}).get("name")} @ {g.get("home_team", {}).get("name")}')
                print(f'  Date: {g.get("date")}')
        except Exception as e:
            print(f'{sport}: ERROR - {str(e)[:80]}')

if __name__ == '__main__':
    asyncio.run(test())
