#!/usr/bin/env python
"""Check database state"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.models.db_models import Prediction
from sqlalchemy import select, text
from datetime import datetime

async def check_db():
    """Check database state"""
    async with AsyncSessionLocal() as session:
        try:
            # Check if table exists
            result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='predictions'"))
            table_exists = result.fetchone() is not None
            print(f"Predictions table exists: {table_exists}")
            
            if table_exists:
                # Count predictions
                stmt = select(Prediction)
                result = await session.execute(stmt)
                predictions = result.scalars().all()
                print(f"Total predictions: {len(predictions)}")
                
                # Count resolved
                stmt = select(Prediction).filter(Prediction.resolved_at.isnot(None))
                result = await session.execute(stmt)
                resolved = result.scalars().all()
                print(f"Resolved predictions: {len(resolved)}")
                
                # Show sample
                if predictions:
                    p = predictions[0]
                    print(f"\nSample prediction:")
                    print(f"  ID: {p.id}")
                    print(f"  Sport: {p.sport}")
                    print(f"  Created: {p.created_at}")
                    print(f"  Resolved: {p.resolved_at}")
                    print(f"  Result: {p.result}")
            
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_db())
