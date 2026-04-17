#!/usr/bin/env python3
"""
Database Performance Indexing Script
Applies essential indexes to PostgreSQL for faster queries
"""

import asyncio
import sys
from datetime import datetime

async def apply_indexes():
    """Apply performance indexes to database"""
    try:
        # Import database utilities
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        
        # Docker internal database connection
        DATABASE_URL = "postgresql+asyncpg://postgres:sports_predictions_password@postgres:5432/sports_predictions"
        
        print("\n" + "="*70)
        print("📊 DATABASE PERFORMANCE INDEXES")
        print("="*70)
        print(f"⏰ Started: {datetime.now().isoformat()}")
        print(f"📡 Database: postgres://[hidden]@postgres:5432/sports_predictions\n")
        
        # Create engine
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        # Define indexes to create
        indexes = [
            # Predictions table (most critical for API queries)
            ("idx_predictions_sport_key", "CREATE INDEX IF NOT EXISTS idx_predictions_sport_key ON predictions(sport_key)"),
            ("idx_predictions_event_id", "CREATE INDEX IF NOT EXISTS idx_predictions_event_id ON predictions(event_id)"),
            ("idx_predictions_created_at", "CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at)"),
            ("idx_predictions_resolved_at", "CREATE INDEX IF NOT EXISTS idx_predictions_resolved_at ON predictions(resolved_at)"),
            ("idx_predictions_player_market", "CREATE INDEX IF NOT EXISTS idx_predictions_player_market ON predictions(player, market_key)"),
            
            # Users table (for authentication and tier lookups)
            ("idx_users_tier", "CREATE INDEX IF NOT EXISTS idx_users_tier ON users(subscription_tier)"),
            ("idx_users_created_at", "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)"),
            ("idx_users_club_100", "CREATE INDEX IF NOT EXISTS idx_users_club_100 ON users(club_100_unlocked)"),
            
            # User predictions (for tracking unlocked picks)
            ("idx_user_predictions_user_id", "CREATE INDEX IF NOT EXISTS idx_user_predictions_user_id ON user_predictions(user_id)"),
            ("idx_user_predictions_created_at", "CREATE INDEX IF NOT EXISTS idx_user_predictions_created_at ON user_predictions(created_at)"),
            ("idx_user_predictions_prediction_id", "CREATE INDEX IF NOT EXISTS idx_user_predictions_prediction_id ON user_predictions(prediction_id)"),
            
            # Prediction records (for analytics and accuracy tracking)
            ("idx_prediction_records_user_id", "CREATE INDEX IF NOT EXISTS idx_prediction_records_user_id ON prediction_records(user_id)"),
            ("idx_prediction_records_created_at", "CREATE INDEX IF NOT EXISTS idx_prediction_records_created_at ON prediction_records(date)"),
        ]
        
        print(f"📋 Indexes to create: {len(indexes)}\n")
        
        async with engine.connect() as conn:
            created = 0
            skipped = 0
            failed = 0
            
            for idx_name, idx_sql in indexes:
                try:
                    await conn.execute(text(idx_sql))
                    await conn.commit()
                    print(f"✅ {idx_name:<40} Created")
                    created += 1
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print(f"⏭️  {idx_name:<40} Skipped (already exists)")
                        skipped += 1
                    elif "does not exist" in str(e).lower():
                        print(f"❌ {idx_name:<40} Skipped (table not ready)")
                        skipped += 1
                    else:
                        print(f"❌ {idx_name:<40} Failed: {str(e)[:50]}")
                        failed += 1
        
        print("\n" + "="*70)
        print(f"📊 RESULTS:")
        print(f"   ✅ Created: {created}")
        print(f"   ⏭️  Skipped: {skipped}")
        print(f"   ❌ Failed:  {failed}")
        print(f"⏰ Completed: {datetime.now().isoformat()}")
        print("="*70 + "\n")
        
        await engine.dispose()
        return created > 0 or skipped > 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        print("⚠️  This is normal if the database tables haven't been created yet.")
        print("    The application will create tables automatically on first run.\n")
        return False

if __name__ == "__main__":
    success = asyncio.run(apply_indexes())
    sys.exit(0 if success else 1)
