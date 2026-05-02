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
                await session.execute(text('''
                    INSERT INTO player_records (id, name, sport_key, team_key, position, nba_id, nfl_id, nhl_id, mlb_id, soccer_id, created_at, updated_at)
                    VALUES (:id, :name, :sport_key, :team_key, :position, :nba_id, :nfl_id, :nhl_id, :mlb_id, :soccer_id, :created_at, :updated_at)
                '''), player)

            # Import game logs
            for log in data['game_logs']:
                await session.execute(text('''
                    INSERT INTO player_game_logs (id, player_id, date, opponent, event_id, stats, created_at)
                    VALUES (:id, :player_id, :date, :opponent, :event_id, :stats, :created_at)
                '''), log)

            await session.commit()
            print(f"Imported {len(data['players'])} players, {len(data['game_logs'])} game logs")

        except Exception as e:
            await session.rollback()
            print(f"Error importing data: {e}")
            raise

if __name__ == '__main__':
    asyncio.run(import_data())