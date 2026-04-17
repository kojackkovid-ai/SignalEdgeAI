"""
Migration script to add Club 100 columns to users table
Run this script to update the database schema
"""

import asyncio
import sys
from sqlalchemy import text
from app.database import engine

async def run_migration():
    """Add the missing Club 100 columns to users table"""
    async with engine.begin() as conn:
        try:
            # Check which database we're using
            result = await conn.execute(text("SELECT sqlite_version()"))
            result.fetchone()
            is_sqlite = True
            print("Using SQLite database")
        except:
            is_sqlite = False
            print("Using non-SQLite database (PostgreSQL/MySQL)")
        
        # Get existing columns in users table
        if is_sqlite:
            result = await conn.execute(text("PRAGMA table_info(users)"))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]
        else:
            result = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"
            ))
            column_names = [row[0] for row in result.fetchall()]
        
        print(f"Existing columns: {column_names}")
        
        # Add missing columns
        columns_to_add = {
            'club_100_unlocked': 'BOOLEAN DEFAULT 0',
            'club_100_unlocked_at': 'DATETIME',
            'club_100_picks_available': 'INTEGER DEFAULT 0'
        }
        
        for column_name, column_def in columns_to_add.items():
            if column_name not in column_names:
                try:
                    sql = f"ALTER TABLE users ADD COLUMN {column_name} {column_def}"
                    print(f"Executing: {sql}")
                    await conn.execute(text(sql))
                    print(f"✅ Added column: {column_name}")
                except Exception as e:
                    print(f"❌ Error adding column {column_name}: {e}")
                    return False
            else:
                print(f"⏭️ Column {column_name} already exists")
        
        await conn.commit()
        print("\n✅ Migration completed successfully!")
        return True

if __name__ == "__main__":
    try:
        success = asyncio.run(run_migration())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
