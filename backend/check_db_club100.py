import asyncio
from app.database import get_db
from app.models.prediction_records import PlayerGameLog, PlayerRecord
from sqlalchemy import text

async def check_db():
    async for session in get_db():
        # Count player game logs
        result = await session.execute(text("SELECT COUNT(*) FROM player_game_logs"))
        log_count = result.scalar()
        print(f"Player game logs count: {log_count}")

        # Count player records
        result2 = await session.execute(text("SELECT COUNT(*) FROM player_records"))
        player_count = result2.scalar()
        print(f"Player records count: {player_count}")

        # Check recent logs
        result3 = await session.execute(text("""
            SELECT sport_key, COUNT(*) as count
            FROM player_records
            GROUP BY sport_key
        """))
        sport_counts = result3.fetchall()
        print("Player records by sport:")
        for sport, count in sport_counts:
            print(f"  {sport}: {count}")

        # Check if any players have nba_id
        result4 = await session.execute(text("""
            SELECT COUNT(*) FROM player_records
            WHERE nba_id IS NOT NULL AND nba_id != ''
        """))
        nba_count = result4.scalar()
        print(f"Players with nba_id: {nba_count}")

        # Check recent game logs
        result5 = await session.execute(text("""
            SELECT COUNT(*) FROM player_game_logs
            WHERE date >= CURRENT_DATE - INTERVAL '30 days'
        """))
        recent_logs = result5.scalar()
        print(f"Game logs in last 30 days: {recent_logs}")

        break

if __name__ == "__main__":
    asyncio.run(check_db())