#!/usr/bin/env python
"""Mimic the analytics endpoint logic directly"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_analytics():
    """Test the exact logic from the analytics endpoint"""
    from app.database import get_db, AsyncSessionLocal
    from app.models.db_models import Prediction
    from sqlalchemy import select, text
    
    print("=" * 60)
    print("Testing analytics logic directly")
    print("=" * 60)
    
    # Method 1: Using AsyncSessionLocal directly (like my test script)
    print("\nMethod 1: Using AsyncSessionLocal directly")
    async with AsyncSessionLocal() as session:
        stmt = select(Prediction)
        result = await session.execute(stmt)
        preds = result.scalars().all()
        print(f"  Total predictions: {len(preds)}")
    
    # Method 2: Using get_db() generator (like the endpoint)
    print("\nMethod 2: Using get_db() dependency generator")
    async for db in get_db():
        stmt = select(Prediction)
        result = await db.execute(stmt)
        preds = result.scalars().all()
        print(f"  Total predictions: {len(preds)}")
        
        # Also try the raw SQL count
        try:
            raw_result = await db.execute(text("SELECT COUNT(*) as count FROM predictions"))
            raw_count = raw_result.fetchone()[0]
            print(f"  Raw SQL COUNT: {raw_count}")
        except Exception as e:
            print(f"  Raw SQL failed: {e}")
        
        break  # Only iterate once since the generator has cleanup logic
    
    # Method 3: Test with cutoff filter like the endpoint does
    print("\nMethod 3: Using filtered query with cutoff_date")
    days = 90
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    print(f"  Cutoff date: {cutoff_date}")
    
    async with AsyncSessionLocal() as session:
        query = select(Prediction).filter(
            Prediction.created_at >= cutoff_date,
            Prediction.resolved_at.isnot(None)
        )
        result = await session.execute(query)
        preds = result.scalars().all()
        print(f"  Filtered predictions: {len(preds)}")
        
        # Show some details
        if preds:
            p = preds[0]
            print(f"    Sample: created={p.created_at}, resolved={p.resolved_at}, result={p.result}")

if __name__ == "__main__":
    asyncio.run(test_analytics())
