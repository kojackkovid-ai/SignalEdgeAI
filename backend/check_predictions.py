#!/usr/bin/env python3
"""
Simple test to check if resolution service can find predictions
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

async def check_predictions():
    """Check what predictions exist in the database"""
    print("🔍 Checking predictions in database...")

    try:
        from app.database import get_db
        from app.models.prediction_records import PredictionRecord
        from sqlalchemy import select

        async for db in get_db():
            try:
                # Check total predictions
                result = await db.execute(select(PredictionRecord))
                all_predictions = result.scalars().all()
                print(f"📊 Total prediction_records: {len(all_predictions)}")

                # Check pending predictions
                pending_result = await db.execute(
                    select(PredictionRecord).where(PredictionRecord.outcome == 'pending')
                )
                pending = pending_result.scalars().all()
                print(f"⏳ Pending predictions: {len(pending)}")

                # Check resolved predictions
                resolved_result = await db.execute(
                    select(PredictionRecord).where(PredictionRecord.outcome.in_(['hit', 'miss']))
                )
                resolved = resolved_result.scalars().all()
                print(f"✅ Resolved predictions: {len(resolved)}")

                # Show sample of each
                if pending:
                    print("📋 Sample pending predictions:")
                    for p in pending[:2]:
                        print(f"  - {p.sport_key}: {p.home_team} vs {p.away_team} ({p.prediction_type})")

                if resolved:
                    print("📋 Sample resolved predictions:")
                    for p in resolved[:2]:
                        print(f"  - {p.sport_key}: {p.home_team} vs {p.away_team} ({p.prediction_type}) -> {p.outcome}")

            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Current directory:", os.getcwd())

if __name__ == "__main__":
    asyncio.run(check_predictions())