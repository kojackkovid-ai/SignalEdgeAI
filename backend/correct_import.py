import asyncio
import sys
import json
sys.path.append('/app')

from app.database import engine
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def import_data():
    # Load the exported data
    with open('/tmp/player_data_export.json', 'r') as f:
        data = json.load(f)

    async with AsyncSession(engine) as session:
        try:
            # Clear existing data
            await session.execute(text('DELETE FROM player_game_logs'))
            await session.execute(text('DELETE FROM player_season_stats'))
            await session.execute(text('DELETE FROM player_records'))

            # Import players
            for player in data['players']:
                # Handle None values and map to correct column names
                player_data = {
                    'id': player.get('id'),
                    'name': player.get('name'),
                    'sport_key': player.get('sport_key'),
                    'team_key': player.get('team_key'),
                    'position': player.get('position'),
                    'nba_id': player.get('nba_id'),
                    'nfl_id': player.get('nfl_id'),
                    'nhl_id': player.get('nhl_id'),
                    'mlb_id': player.get('mlb_id'),
                    'external_ids': player.get('external_ids'),
                    'created_at': player.get('created_at'),
                    'updated_at': player.get('updated_at')
                }

                await session.execute(text('''
                    INSERT INTO player_records (id, name, sport_key, team_key, position, nba_id, nfl_id, nhl_id, mlb_id, external_ids, created_at, updated_at)
                    VALUES (:id, :name, :sport_key, :team_key, :position, :nba_id, :nfl_id, :nhl_id, :mlb_id, :external_ids, :created_at, :updated_at)
                '''), player_data)

            # Import game logs
            for log in data['game_logs']:
                log_data = {
                    'id': log.get('id'),
                    'player_id': log.get('player_id'),
                    'date': log.get('date'),
                    'opponent': log.get('opponent'),
                    'event_id': log.get('event_id'),
                    'stats': json.dumps(log.get('stats')) if log.get('stats') else None,
                    'created_at': log.get('created_at')
                }

                await session.execute(text('''
                    INSERT INTO player_game_logs (id, player_id, date, opponent, event_id, stats, created_at)
                    VALUES (:id, :player_id, :date, :opponent, :event_id, :stats, :created_at)
                '''), log_data)

            await session.commit()
            print(f"Imported {len(data['players'])} players, {len(data['game_logs'])} game logs")

        except Exception as e:
            await session.rollback()
            print(f"Error importing data: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == '__main__':
    asyncio.run(import_data())