"""
Migration script to add is_club_100_pick column to predictions table.

This handles both SQLite and PostgreSQL databases.
Run: python migrate_add_club100_tracking.py
"""

import asyncio
import logging
from sqlalchemy import text, inspect
from sqlalchemy.engine import Connection
from app.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_column_sync(conn: Connection) -> bool:
    """Check if is_club_100_pick column exists (sync version)"""
    inspector = inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('predictions')]
    return 'is_club_100_pick' in columns


async def add_column_to_predictions():
    """Add is_club_100_pick column to predictions table"""
    
    async with engine.begin() as conn:
        # Check if column already exists using run_sync
        exists = await conn.run_sync(check_column_sync)
        
        if exists:
            logger.info("✅ Column 'is_club_100_pick' already exists in predictions table")
            return
        
        logger.info("Adding 'is_club_100_pick' column to predictions table...")
        
        # Get database type
        db_url = str(engine.url)
        is_sqlite = 'sqlite' in db_url
        is_postgres = 'postgresql' in db_url or 'postgres' in db_url
        
        try:
            if is_sqlite:
                # SQLite migration
                logger.info("✓ Detected SQLite database")
                await conn.execute(text("""
                    ALTER TABLE predictions 
                    ADD COLUMN is_club_100_pick BOOLEAN DEFAULT 0
                """))
                logger.info("✅ Added is_club_100_pick column to SQLite predictions table")
                
            elif is_postgres:
                # PostgreSQL migration
                logger.info("✓ Detected PostgreSQL database")
                await conn.execute(text("""
                    ALTER TABLE predictions 
                    ADD COLUMN is_club_100_pick BOOLEAN DEFAULT FALSE
                """))
                logger.info("✅ Added is_club_100_pick column to PostgreSQL predictions table")
                
                # Add index for better query performance
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_predictions_is_club_100_pick 
                    ON predictions(is_club_100_pick)
                """))
                logger.info("✅ Created index on is_club_100_pick column")
            else:
                logger.warning(f"⚠️ Unknown database type: {db_url}")
                return
            
            await conn.commit()
            logger.info("✅ Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error during migration: {e}")
            await conn.rollback()
            raise


async def main():
    """Main migration function"""
    try:
        logger.info("=" * 60)
        logger.info("Starting Club 100 Tracking Migration")
        logger.info("=" * 60)
        
        await add_column_to_predictions()
        
        logger.info("=" * 60)
        logger.info("✅ Migration completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
