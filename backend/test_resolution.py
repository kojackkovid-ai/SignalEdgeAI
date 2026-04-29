#!/usr/bin/env python3
"""
Quick test to resolve pending predictions
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

async def test_resolution():
    """Test the prediction resolution service"""
    print("🔄 Testing prediction resolution...")

    try:
        from app.database import get_db
        from app.services.prediction_resolution_service import PredictionResolutionService

        async for db in get_db():
            try:
                service = PredictionResolutionService()
                result = await service.resolve_all_pending_predictions(db)

                print(f"✅ Resolution result: {result}")

                # Check how many pending predictions remain
                from app.models.prediction_records import PredictionRecord
                from sqlalchemy import select

                pending_result = await db.execute(
                    select(PredictionRecord).where(PredictionRecord.outcome == 'pending')
                )
                pending = pending_result.scalars().all()
                print(f"📊 Remaining pending predictions: {len(pending)}")

                # Show a few examples
                if pending:
                    print("📋 Sample pending predictions:")
                    for p in pending[:3]:
                        print(f"  - {p.sport_key}: {p.home_team} vs {p.away_team} ({p.prediction_type})")

            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Current directory:", os.getcwd())
        print("Python path:", sys.path)

if __name__ == "__main__":
    asyncio.run(test_resolution())