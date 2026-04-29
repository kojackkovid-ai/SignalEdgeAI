import asyncio
import sys
import os
sys.path.insert(0, os.getcwd())
from app.database import get_db
from app.services.club_100_service import Club100Service
from app.services.espn_player_stats_service import get_player_stats_service

async def main():
    service = Club100Service()
    espn = get_player_stats_service()
    async for db in get_db():
        for sport in ['nba', 'nfl', 'mlb', 'nhl']:
            games = await espn.get_today_games_player_stats(sport)
            print('=== SPORT', sport, 'GAMES', len(games), '===')
            if not games:
                continue
            for game in games[:1]:
                print('GAME:', game.get('game', {}).get('name'))
                for li, leader in enumerate(game.get('leaders', [])[:15]):
                    athlete = leader.get('athlete', {})
                    name = athlete.get('fullName') or athlete.get('displayName')
                    aid = athlete.get('id')
                    team_name = leader.get('team_name')
                    team_abbrev = leader.get('team_abbrev')
                    category = leader.get('category')
                    value = leader.get('value')
                    player_record = await service._find_player_record(db, sport, aid, name, team_name, team_abbrev)
                    logs = []
                    if player_record:
                        logs = await service._get_player_recent_game_logs(db, player_record.id, 6)
                    print(f'LEADER {li}:', name, 'id=', aid, 'cat=', category, 'val=', value, 'team=', team_name, team_abbrev, 'record=', bool(player_record), 'logs=', len(logs))
                    if not player_record:
                        if sport == 'nba':
                            # print candidate lookup failure details
                            from app.models.prediction_records import PlayerRecord
                            result = await db.execute(__import__('sqlalchemy').select(PlayerRecord).where(PlayerRecord.sport_key == service.SPORT_DB_KEYS.get(sport), PlayerRecord.name.ilike(f'%{name}%')))
                            matches = result.scalars().all()
                            print('    DB matches by name:', len(matches))
                            for m in matches[:3]:
                                print('      ', m.id, m.name, m.team_key, m.nba_id)
                print('')
        data = await service.get_fresh_club_100_data(db)
        print('FRESH CLUB100 DATA:')
        print({sport: len(players) for sport, players in data.items()})
        break

asyncio.run(main())
