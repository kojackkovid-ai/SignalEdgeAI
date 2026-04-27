#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, 'backend')

from app.services.espn_prediction_service import ESPNPredictionService

async def test():
    service = ESPNPredictionService()
    sport_key = 'soccer_ita.1'
    home_team_id = '239'
    away_team_id = '110'
    
    home, away = await asyncio.gather(
        service._get_team_roster(sport_key, home_team_id),
        service._get_team_roster(sport_key, away_team_id),
        return_exceptions=True
    )
    
    home_count = len(home) if isinstance(home, list) else "ERROR"
    away_count = len(away) if isinstance(away, list) else "ERROR"
    
    print(f'Home roster: {type(home).__name__} with {home_count} players')
    print(f'Away roster: {type(away).__name__} with {away_count} players')
    
    if isinstance(home, Exception):
        print(f'  Home error: {home}')
    if isinstance(away, Exception):
        print(f'  Away error: {away}')

asyncio.run(test())
