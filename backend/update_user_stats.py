#!/usr/bin/env python3
"""
Update user stats for migrated predictions
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

async def update_user_stats():
    """Update user statistics after migration"""
    print("📊 Updating user statistics...")

    try:
        from app.database import get_db
        from app.services.prediction_resolution_service import PredictionResolutionService

        async for db in get_db():
            try:
                service = PredictionResolutionService()
                await service._update_user_stats(db)

                print("✅ User statistics updated")

                # Check results
                from app.models.db_models import User
                from sqlalchemy import select

                result = await db.execute(select(User).limit(5))
                users = result.scalars().all()

                print("📋 User statistics:")
                for user in users:
                    print(f"  {user.username}: {user.total_predictions} predictions, {user.win_rate:.1%} win rate, {user.roi:.1f}% ROI")

            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Current directory:", os.getcwd())

if __name__ == "__main__":
    asyncio.run(update_user_stats())