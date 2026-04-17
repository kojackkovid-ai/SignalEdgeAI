#!/usr/bin/env python
"""Simple database check"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting database check...")

# Check database file
db_path = "sports_predictions.db"
if os.path.exists(db_path):
    size = os.path.getsize(db_path)
    print(f"Database file exists: {db_path} ({size} bytes)")
else:
    print(f"Database file NOT found: {db_path}")

# Try to import and check
try:
    import asyncio
    from app.database import AsyncSessionLocal
    from app.models.db_models import Prediction
    from sqlalchemy import select, text
    
    async def check():
        async with AsyncSessionLocal() as session:
            # Try raw SQL first
            try:
                result = await session.execute(text("SELECT COUNT(*) FROM predictions"))
                count = result.scalar()
                print(f"Raw SQL COUNT: {count}")
            except Exception as e:
                print(f"Raw SQL failed: {e}")
            
            # Try ORM
            try:
                stmt = select(Prediction)
                result = await session.execute(stmt)
                preds = result.scalars().all()
                print(f"ORM query result: {len(preds)} rows")
            except Exception as e:
                print(f"ORM query failed: {e}")
    
    asyncio.run(check())
    print("Check completed")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
