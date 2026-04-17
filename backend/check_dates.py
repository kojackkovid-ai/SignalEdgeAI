#!/usr/bin/env python
"""Check prediction created_at dates"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.models.db_models import Prediction
from sqlalchemy import select

async def check():
    """Check created_at dates"""
    async with AsyncSessionLocal() as session:
        # Get all resolved predictions
        stmt = select(Prediction).filter(Prediction.resolved_at.isnot(None))
        result = await session.execute(stmt)
        resolved = result.scalars().all()
        print(f"Total resolved: {len(resolved)}")
        
        if resolved:
            oldest = min(p.created_at for p in resolved if p.created_at)
            newest = max(p.created_at for p in resolved if p.created_at)
            print(f"Oldest created_at: {oldest}")
            print(f"Newest created_at: {newest}")
            
            cutoff_90 = datetime.utcnow() - timedelta(days=90)
            cutoff_365 = datetime.utcnow() - timedelta(days=365)
            
            print(f"\nCurrent time (UTC): {datetime.utcnow()}")
            print(f"90-day cutoff: {cutoff_90}")
            print(f"365-day cutoff: {cutoff_365}")
            
            within_90 = sum(1 for p in resolved if p.created_at and p.created_at >= cutoff_90)
            within_365 = sum(1 for p in resolved if p.created_at and p.created_at >= cutoff_365)
            
            print(f"\nResolved within 90 days: {within_90}")
            print(f"Resolved within 365 days: {within_365}")
            
            # Show distribution
            print(f"\nDate distribution:")
            for i, p in enumerate(resolved[:10]):
                age_days = (datetime.utcnow() - p.created_at).days if p.created_at else None
                print(f"  {i+1}. created={p.created_at}, age={age_days} days, result={p.result}")

if __name__ == "__main__":
    asyncio.run(check())
