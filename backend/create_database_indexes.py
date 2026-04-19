#!/usr/bin/env python3
"""
Database Index Creation Script
Creates all necessary indexes for performance optimization

Run this script once after database setup:
    python create_database_indexes.py
"""

import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import engine

logger_output = []

def log(message: str, level: str = "INFO"):
    """Log message with level"""
    output = f"[{level}] {message}"
    logger_output.append(output)
    print(output)

async def create_indexes_postgresql():
    """Create indexes for PostgreSQL"""
    
    log("Creating PostgreSQL indexes...")
    
    # Critical indexes for performance
    index_definitions = [
        # User indexes
        ('idx_user_email', 'CREATE UNIQUE INDEX IF NOT EXISTS idx_user_email ON "user" (email)'),
        ('idx_user_created_at', 'CREATE INDEX IF NOT EXISTS idx_user_created_at ON "user" (created_at DESC)'),
        ('idx_user_subscription_tier', 'CREATE INDEX IF NOT EXISTS idx_user_subscription_tier ON "user" (subscription_tier)'),
        ('idx_user_active', 'CREATE INDEX IF NOT EXISTS idx_user_active ON "user" (is_active)'),
        
        # Prediction indexes - MOST IMPORTANT FOR PERFORMANCE
        ('idx_prediction_sport', 'CREATE INDEX IF NOT EXISTS idx_prediction_sport ON prediction (sport)'),
        ('idx_prediction_user_id', 'CREATE INDEX IF NOT EXISTS idx_prediction_user_id ON prediction (user_id)'),
        ('idx_prediction_created_at', 'CREATE INDEX IF NOT EXISTS idx_prediction_created_at ON prediction (created_at DESC)'),
        ('idx_prediction_confidence', 'CREATE INDEX IF NOT EXISTS idx_prediction_confidence ON prediction (confidence DESC)'),
        ('idx_prediction_resolved', 'CREATE INDEX IF NOT EXISTS idx_prediction_resolved ON prediction (resolved_at)'),
        ('idx_prediction_result', 'CREATE INDEX IF NOT EXISTS idx_prediction_result ON prediction (result)'),
        
        # Composite indexes for common query patterns
        ('idx_prediction_sport_created', 'CREATE INDEX IF NOT EXISTS idx_prediction_sport_created ON prediction (sport, created_at DESC)'),
        ('idx_prediction_user_confirmed', 'CREATE INDEX IF NOT EXISTS idx_prediction_user_confirmed ON prediction (user_id, confirmed)'),
        ('idx_prediction_sport_confidence', 'CREATE INDEX IF NOT EXISTS idx_prediction_sport_confidence ON prediction (sport, confidence DESC)'),
        
        # Player props indexes
        ('idx_props_sport', 'CREATE INDEX IF NOT EXISTS idx_props_sport ON player_props (sport)'),
        ('idx_props_event_id', 'CREATE INDEX IF NOT EXISTS idx_props_event_id ON player_props (event_id)'),
        ('idx_props_player_name', 'CREATE INDEX IF NOT EXISTS idx_props_player_name ON player_props (player_name)'),
        ('idx_props_market', 'CREATE INDEX IF NOT EXISTS idx_props_market ON player_props (market)'),
        ('idx_props_created_at', 'CREATE INDEX IF NOT EXISTS idx_props_created_at ON player_props (created_at DESC)'),
        ('idx_props_confidence', 'CREATE INDEX IF NOT EXISTS idx_props_confidence ON player_props (confidence DESC)'),
        
        # User predictions/follows indexes
        ('idx_user_pred_user_id', 'CREATE INDEX IF NOT EXISTS idx_user_pred_user_id ON user_predictions (user_id)'),
        ('idx_user_pred_prediction_id', 'CREATE INDEX IF NOT EXISTS idx_user_pred_prediction_id ON user_predictions (prediction_id)'),
        ('idx_user_pred_created_at', 'CREATE INDEX IF NOT EXISTS idx_user_pred_created_at ON user_predictions (created_at DESC)'),
        
        # Token blacklist indexes
        ('idx_token_user_id', 'CREATE INDEX IF NOT EXISTS idx_token_user_id ON token_blacklist (user_id)'),
        ('idx_token_expires_at', 'CREATE INDEX IF NOT EXISTS idx_token_expires_at ON token_blacklist (expires_at)'),
        
        # Subscription history indexes
        ('idx_sub_user_id', 'CREATE INDEX IF NOT EXISTS idx_sub_user_id ON subscription_history (user_id)'),
        ('idx_sub_created_at', 'CREATE INDEX IF NOT EXISTS idx_sub_created_at ON subscription_history (created_at DESC)'),
        ('idx_sub_tier', 'CREATE INDEX IF NOT EXISTS idx_sub_tier ON subscription_history (tier)'),
    ]
    
    async with engine.begin() as conn:
        created_count = 0
        skipped_count = 0
        failed_count = 0
        
        for index_name, index_sql in index_definitions:
            try:
                await conn.execute(text(index_sql))
                log(f"✓ Created index: {index_name}", "SUCCESS")
                created_count += 1
            except Exception as e:
                if "already exists" in str(e).lower():
                    log(f"⊘ Skipped index (already exists): {index_name}", "INFO")
                    skipped_count += 1
                else:
                    log(f"✗ Failed to create index {index_name}: {str(e)}", "ERROR")
                    failed_count += 1
        
        log(f"\nIndex Creation Summary:", "INFO")
        log(f"  Created: {created_count}", "INFO")
        log(f"  Skipped (already exist): {skipped_count}", "INFO")
        log(f"  Failed: {failed_count}", "ERROR" if failed_count > 0 else "INFO")
        
        return created_count > 0 or skipped_count > 0

async def create_indexes_sqlite():
    """Create indexes for SQLite"""
    
    log("Creating SQLite indexes...")
    
    index_definitions = [
        # User indexes
        ('idx_user_email', 'CREATE UNIQUE INDEX IF NOT EXISTS idx_user_email ON user (email)'),
        ('idx_user_created_at', 'CREATE INDEX IF NOT EXISTS idx_user_created_at ON user (created_at DESC)'),
        ('idx_user_subscription_tier', 'CREATE INDEX IF NOT EXISTS idx_user_subscription_tier ON user (subscription_tier)'),
        ('idx_user_active', 'CREATE INDEX IF NOT EXISTS idx_user_active ON user (is_active)'),
        
        # Prediction indexes
        ('idx_prediction_sport', 'CREATE INDEX IF NOT EXISTS idx_prediction_sport ON prediction (sport)'),
        ('idx_prediction_user_id', 'CREATE INDEX IF NOT EXISTS idx_prediction_user_id ON prediction (user_id)'),
        ('idx_prediction_created_at', 'CREATE INDEX IF NOT EXISTS idx_prediction_created_at ON prediction (created_at DESC)'),
        ('idx_prediction_confidence', 'CREATE INDEX IF NOT EXISTS idx_prediction_confidence ON prediction (confidence DESC)'),
        ('idx_prediction_resolved', 'CREATE INDEX IF NOT EXISTS idx_prediction_resolved ON prediction (resolved_at)'),
        ('idx_prediction_result', 'CREATE INDEX IF NOT EXISTS idx_prediction_result ON prediction (result)'),
        
        # Composite indexes
        ('idx_prediction_sport_created', 'CREATE INDEX IF NOT EXISTS idx_prediction_sport_created ON prediction (sport, created_at)'),
        ('idx_prediction_user_confirmed', 'CREATE INDEX IF NOT EXISTS idx_prediction_user_confirmed ON prediction (user_id, confirmed)'),
        
        # Player props indexes
        ('idx_props_sport', 'CREATE INDEX IF NOT EXISTS idx_props_sport ON player_props (sport)'),
        ('idx_props_event_id', 'CREATE INDEX IF NOT EXISTS idx_props_event_id ON player_props (event_id)'),
        ('idx_props_player_name', 'CREATE INDEX IF NOT EXISTS idx_props_player_name ON player_props (player_name)'),
        ('idx_props_market', 'CREATE INDEX IF NOT EXISTS idx_props_market ON player_props (market)'),
        ('idx_props_created_at', 'CREATE INDEX IF NOT EXISTS idx_props_created_at ON player_props (created_at DESC)'),
        
        # User predictions indexes
        ('idx_user_pred_user_id', 'CREATE INDEX IF NOT EXISTS idx_user_pred_user_id ON user_predictions (user_id)'),
        ('idx_user_pred_prediction_id', 'CREATE INDEX IF NOT EXISTS idx_user_pred_prediction_id ON user_predictions (prediction_id)'),
        ('idx_user_pred_created_at', 'CREATE INDEX IF NOT EXISTS idx_user_pred_created_at ON user_predictions (created_at DESC)'),
    ]
    
    async with engine.begin() as conn:
        created_count = 0
        skipped_count = 0
        failed_count = 0
        
        for index_name, index_sql in index_definitions:
            try:
                await conn.execute(text(index_sql))
                log(f"✓ Created index: {index_name}", "SUCCESS")
                created_count += 1
            except Exception as e:
                if "already exists" in str(e).lower():
                    log(f"⊘ Skipped index (already exists): {index_name}", "INFO")
                    skipped_count += 1
                else:
                    log(f"✗ Failed to create index {index_name}: {str(e)}", "ERROR")
                    failed_count += 1
        
        log(f"\nIndex Creation Summary:", "INFO")
        log(f"  Created: {created_count}", "INFO")
        log(f"  Skipped (already exist): {skipped_count}", "INFO")
        log(f"  Failed: {failed_count}", "ERROR" if failed_count > 0 else "INFO")
        
        return created_count > 0 or skipped_count > 0

async def verify_indexes():
    """Verify indexes were created"""
    
    log("\nVerifying indexes...", "INFO")
    
    async with engine.begin() as conn:
        # Check if PostgreSQL or SQLite
        try:
            await conn.execute(text("SELECT sqlite_version()"))
            # SQLite
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='index'"))
            indexes = result.fetchall()
            log(f"✓ Found {len(indexes)} indexes in database", "SUCCESS")
            for idx in indexes:
                log(f"  - {idx[0]}", "INFO")
        except:
            # PostgreSQL
            result = await conn.execute(text(
                "SELECT indexname FROM pg_indexes WHERE schemaname='public' ORDER BY indexname"
            ))
            indexes = result.fetchall()
            log(f"✓ Found {len(indexes)} indexes in database", "SUCCESS")
            for idx in indexes[:10]:  # Show first 10
                log(f"  - {idx[0]}", "INFO")
            if len(indexes) > 10:
                log(f"  ... and {len(indexes) - 10} more", "INFO")

async def main():
    """Main execution"""
    
    log("=" * 70, "INFO")
    log("DATABASE INDEX CREATION SCRIPT", "INFO")
    log("=" * 70, "INFO")
    log(f"Database URL: {settings.database_url}", "INFO")
    log("", "INFO")
    
    try:
        # Detect database type
        async with engine.begin() as conn:
            try:
                await conn.execute(text("SELECT sqlite_version()"))
                is_sqlite = True
            except:
                is_sqlite = False
        
        # Create indexes
        if is_sqlite:
            success = await create_indexes_sqlite()
        else:
            success = await create_indexes_postgresql()
        
        # Verify
        await verify_indexes()
        
        if success:
            log("\n✅ Index creation completed successfully!", "SUCCESS")
            return 0
        else:
            log("\n⚠️  Index creation completed with warnings", "WARNING")
            return 0
            
    except Exception as e:
        log(f"\n❌ Error during index creation: {str(e)}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")
        return 1
    finally:
        await engine.dispose()
        log("\n" + "=" * 70, "INFO")

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
