import asyncio
import sys
import json
import os
sys.path.append('.')

from app.database import engine
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def export_data():
    async with AsyncSession(engine) as session:
        # Export player records
        result = await session.execute(text('SELECT * FROM player_records'))
        players = result.fetchall()
        player_data = [dict(row._mapping) for row in players]

        # Export game logs
        result = await session.execute(text('SELECT * FROM player_game_logs'))
        logs = result.fetchall()
        log_data = [dict(row._mapping) for row in logs]

        # Export season stats
        result = await session.execute(text('SELECT * FROM player_season_stats'))
        stats = result.fetchall()
        stats_data = [dict(row._mapping) for row in stats]

        data = {
            'players': player_data,
            'game_logs': log_data,
            'season_stats': stats_data
        }

        with open('player_data_export.json', 'w') as f:
            json.dump(data, f, default=str, indent=2)

        print(f"Exported {len(player_data)} players, {len(log_data)} game logs, {len(stats_data)} season stats")

if __name__ == '__main__':
    asyncio.run(export_data())