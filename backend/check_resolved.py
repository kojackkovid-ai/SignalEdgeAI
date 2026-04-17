#!/usr/bin/env python
"""Check resolved predictions"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.models.db_models import Prediction
from sqlalchemy import select

async def check_resolved():
    """Check resolved predictions"""
    async with AsyncSessionLocal() as session:
        try:
            # Get all resolved predictions
            stmt = select(Prediction).filter(Prediction.resolved_at.isnot(None))
            result = await session.execute(stmt)
            resolved = result.scalars().all()
            print(f"Total resolved predictions: {len(resolved)}")
            print(f"\nSample resolved predictions:")
            
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            print(f"\n90-day cutoff date: {cutoff_date}")
            
            for i, p in enumerate(resolved[:5]):
                within_window = p.created_at >= cutoff_date if p.created_at else False
                print(f"\n  Prediction {i+1}:")
                print(f"    ID: {p.id}")
                print(f"    Sport: {p.sport}")
                print(f"    Created: {p.created_at}")
                print(f"    Within 90 days: {within_window}")
                print(f"    Resolved: {p.resolved_at}")
                print(f"    Result: {p.result}")
            
            # Count resolved within 90 days
            within_90 = sum(1 for p in resolved if p.created_at and p.created_at >= cutoff_date)
            print(f"\n\nResolved predictions within 90 days: {within_90} out of {len(resolved)}")
            
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_resolved())
