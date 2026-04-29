#!/usr/bin/env python3
"""
Test accuracy dashboard endpoints directly
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, AsyncSessionLocal
from app.routes.prediction_history import get_user_stats
from app.routes.analytics import get_platform_metrics
from app.services.auth_service import AuthService

async def test_endpoints():
    """Test the accuracy dashboard endpoints"""
    print("Testing accuracy dashboard endpoints...")

    try:
        # Initialize database
        await init_db()
        print("✓ Database initialized")

        async with AsyncSessionLocal() as db:
            # Test user stats (need a user ID)
            auth_service = AuthService()

            # Get first user from database
            from app.models.db_models import User
            from sqlalchemy import select

            result = await db.execute(select(User).limit(1))
            user = result.scalar_one_or_none()

            if not user:
                print("❌ No users found in database")
                return

            print(f"✓ Testing with user: {user.username} (ID: {user.id})")

            # Test user stats endpoint
            print("\n--- Testing /api/user/predictions/stats ---")
            try:
                # First check what user_id is in the prediction_records
                from app.models.prediction_records import PredictionRecord
                from sqlalchemy import select, func
                
                # Get all user_ids in prediction_records
                result = await db.execute(select(PredictionRecord.user_id).distinct())
                user_ids_in_records = [row[0] for row in result.fetchall()]
                print(f"DEBUG: User IDs in prediction_records: {user_ids_in_records}")
                print(f"DEBUG: Testing with user_id: {user.id}")
                
                # Count predictions for this user
                count_result = await db.execute(
                    select(func.count()).select_from(PredictionRecord).where(
                        PredictionRecord.user_id == user.id
                    )
                )
                pred_count = count_result.scalar() or 0
                print(f"DEBUG: Prediction count for user {user.id}: {pred_count}")
                
                user_stats = await get_user_stats(user.id, db)
                print("✓ User stats retrieved:")
                print(f"  Total: {user_stats.get('total', 0)}")
                print(f"  Hits: {user_stats.get('hits', 0)}")
                print(f"  Misses: {user_stats.get('misses', 0)}")
                print(f"  Win rate: {user_stats.get('win_rate', 0):.1%}")
                print(f"  Avg confidence: {user_stats.get('avg_confidence', 0):.2f}")
            except Exception as e:
                print(f"❌ User stats failed: {e}")
                import traceback
                traceback.print_exc()

            # Test platform metrics endpoint
            print("\n--- Testing /analytics/platform-metrics ---")
            try:
                platform_metrics = await get_platform_metrics(30, False, db)
                print("✓ Platform metrics retrieved:")
                overall = platform_metrics.get('platform_overall', {})
                print(f"  Total predictions: {overall.get('total_predictions', 0)}")
                print(f"  Hits: {overall.get('hits', 0)}")
                print(f"  Misses: {overall.get('misses', 0)}")
                print(f"  Pending: {overall.get('pending', 0)}")
                print(f"  Win rate: {overall.get('win_rate', 0):.1%}")
                print(f"  Avg confidence: {overall.get('avg_confidence', 0):.2f}")

                by_sport = platform_metrics.get('by_sport', {})
                if by_sport:
                    print("  By sport:")
                    for sport, stats in by_sport.items():
                        print(f"    {sport}: {stats.get('total', 0)} predictions, {stats.get('win_rate', 0):.1%} win rate")
                else:
                    print("  No sport breakdown available")

            except Exception as e:
                print(f"❌ Platform metrics failed: {e}")
                import traceback
                traceback.print_exc()

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_endpoints())