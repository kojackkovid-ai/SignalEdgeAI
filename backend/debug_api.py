#!/usr/bin/env python3
"""
Debug why Club 100 is still returning empty
"""
import asyncio
import sys
import os
sys.path.insert(0, '.')

# Get current directory
print(f"Current directory: {os.getcwd()}")
print(f"Current user: {os.getenv('USERNAME')}")
print(f"Files in current dir: {os.listdir('.')[:5]}")

async def debug():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy import select, text
    from app.config import Settings
    from app.services.club_100_service import Club100Service
    
    # Get settings
    settings = Settings()
    db_url = settings.database_url
    print(f"\n✓ Database URL from settings: {db_url}")
    
    # Check if database file exists
    db_file = "./sports_predictions.db"
    if os.path.exists(db_file):
        size = os.path.getsize(db_file)
        print(f"✓ Found {db_file} ({size} bytes)")
    else:
        print(f"✗ NOT FOUND: {db_file}")
        # List db files
        import glob
        dbs = glob.glob("**/*.db", recursive=True)
        print(f"  Found {len(dbs)} .db files: {dbs[:3]}")
    
    # Connect and check
    engine = create_async_engine(db_url, echo=False)
    async_session_local = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_local() as db:
        print(f"\n✓ Connected to database")
        
        # Check game logs
        result = await db.execute(text("SELECT COUNT(*) FROM player_game_logs"))
        count = result.scalar()
        print(f"✓ player_game_logs table: {count} rows")
        
        if count == 0:
            print("✗ Table is empty!")
            
            # Check if other table exists
            try:
                result = await db.execute(text("SELECT COUNT(*) FROM player_game_log"))
                count2  = result.scalar()
                print(f"  player_game_log (no S) exists: {count2} rows")
            except:
                print(f"  player_game_log (no S) does not exist")
        
        # Get sports breakdown
        result = await db.execute(text("""
            SELECT sport_key, COUNT(*) FROM player_game_logs 
            GROUP BY sport_key ORDER BY sport_key
        """))
        sports = result.fetchall()
        print(f"\nSports in database:")
        for sport, cnt in sports:
            print(f"  - {sport}: {cnt}")
        
        # Try Club100Service
        print(f"\nCalling Club100Service...")
        service = Club100Service()
        result = await service.get_club_100_data(db)
        
        total = sum(len(p) for p in result.values())
        print(f"✓ Club100Service returned {total} players")
        
        for sport, players in result.items():
            if players:
                print(f"  {sport}: {len(players)} players")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug())
