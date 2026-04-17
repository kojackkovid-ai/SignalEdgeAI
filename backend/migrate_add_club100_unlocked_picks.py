"""
Migration script to add club_100_unlocked_picks column to users table
This column stores the list of player IDs that users have unlocked for Club 100
Run this script to update the database schema

Usage:
    python -m backend.migrate_add_club100_unlocked_picks
    or
    cd backend && python migrate_add_club100_unlocked_picks.py
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database import engine

async def run_migration():
    """Add the club_100_unlocked_picks column to users table"""
    async with engine.begin() as conn:
        try:
            # Detect database type
            try:
                result = await conn.execute(text("SELECT sqlite_version()"))
                result.fetchone()
                is_sqlite = True
                db_type = "SQLite"
            except:
                is_sqlite = False
                try:
                    result = await conn.execute(text("SELECT version()"))
                    version = result.scalar()
                    db_type = "PostgreSQL" if "PostgreSQL" in str(version) else "MySQL/Unknown"
                except:
                    db_type = "Unknown"
            
            print(f"\n📊 Database Type: {db_type}")
            
            # Get existing columns in users table
            if is_sqlite:
                result = await conn.execute(text("PRAGMA table_info(users)"))
                columns = result.fetchall()
                column_names = [col[1] for col in columns]
            else:
                result = await conn.execute(text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' ORDER BY column_name"
                ))
                column_names = [row[0] for row in result.fetchall()]
            
            print(f"✓ Existing columns in users table: {', '.join(column_names[:5])}... ({len(column_names)} total)")
            
            # Add club_100_unlocked_picks column if missing
            column_name = 'club_100_unlocked_picks'
            
            if column_name in column_names:
                print(f"✓ Column '{column_name}' already exists - no action needed")
                return True
            
            # Determine the correct column definition based on database type
            if is_sqlite:
                column_def = "JSON DEFAULT '[]'"
            else:
                # PostgreSQL and MySQL both support JSON type
                column_def = "JSON DEFAULT '[]'"
            
            try:
                sql = f"ALTER TABLE users ADD COLUMN {column_name} {column_def}"
                print(f"\n🔧 Executing migration:")
                print(f"   {sql}")
                await conn.execute(text(sql))
                await conn.commit()
                print(f"✅ Successfully added column: {column_name}")
                return True
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Error adding column {column_name}: {error_msg}")
                
                # Check if it's already exists error
                if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                    print("   → Column appears to already exist")
                    return True
                else:
                    print(f"   → Please check the error and try again")
                    return False
        
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            return False

async def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("Club 100 Unlocked Picks Migration")
    print("="*60)
    
    success = await run_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("   Users can now login and register.")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        print("   Please check the database and try again.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
