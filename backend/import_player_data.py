import asyncio
import sys
import json
import os
sys.path.append('.')

from app.database import engine
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.prediction_records import PlayerRecord, PlayerGameLog, PlayerSeasonStats

async def import_data():
    # Load the exported data
    with open('player_data_export.json', 'r') as f:
        data = json.load(f)

    async with AsyncSession(engine) as session:
        try:
            # Clear existing data
            await session.execute(text('DELETE FROM player_game_logs'))
            await session.execute(text('DELETE FROM player_season_stats'))
            await session.execute(text('DELETE FROM player_records'))

            # Import players
            for player in data['players']:
                # Convert string dates back to datetime if needed
                if 'created_at' in player and player['created_at']:
                    # Keep as string for now
                    pass
                if 'updated_at' in player and player['updated_at']:
                    pass

                await session.execute(text('''
                    INSERT INTO player_records (id, name, sport_key, team, position, nba_id, nfl_id, nhl_id, mlb_id, soccer_id, created_at, updated_at)
                    VALUES (:id, :name, :sport_key, :team, :position, :nba_id, :nfl_id, :nhl_id, :mlb_id, :soccer_id, :created_at, :updated_at)
                '''), player)

            # Import game logs
            for log in data['game_logs']:
                await session.execute(text('''
                    INSERT INTO player_game_logs (id, player_id, date, opponent, event_id, stats, created_at)
                    VALUES (:id, :player_id, :date, :opponent, :event_id, :stats, :created_at)
                '''), log)

            # Import season stats
            for stat in data['season_stats']:
                await session.execute(text('''
                    INSERT INTO player_season_stats (id, player_id, season, stats, created_at, updated_at)
                    VALUES (:id, :player_id, :season, :stats, :created_at, :updated_at)
                '''), stat)

            await session.commit()
            print(f"Imported {len(data['players'])} players, {len(data['game_logs'])} game logs, {len(data['season_stats'])} season stats")

        except Exception as e:
            await session.rollback()
            print(f"Error importing data: {e}")
            raise

if __name__ == '__main__':
    asyncio.run(import_data())