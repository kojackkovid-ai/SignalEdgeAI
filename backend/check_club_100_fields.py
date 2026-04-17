#!/usr/bin/env python
"""Check current User model columns and add club_100 fields if needed"""
import sys
sys.path.insert(0, '.')

from app.models.db_models import User
from sqlalchemy import inspect, Column, Boolean, DateTime
from datetime import datetime

# Print User table columns
print("\n=== Current User table columns ===")
mapper = inspect(User)
existing_columns = [column.name for column in mapper.columns]

for column in mapper.columns:
    print(f"  ✓ {column.name}: {column.type}")

print("\n=== Checking for Club 100 fields ===")
club_100_fields = ['club_100_unlocked', 'club_100_unlocked_at', 'club_100_picks_available']

for field in club_100_fields:
    if field in existing_columns:
        print(f"  ✓ {field} EXISTS")
    else:
        print(f"  ✗ {field} MISSING - needs migration")

print("\nTo add missing fields, run:")
print("  alembic revision --autogenerate -m 'Add club_100 fields to User'")
print("  alembic upgrade head")
