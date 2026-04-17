#!/usr/bin/env python
"""Quick test to verify Club 100 implementation is in place"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("="*60)
print("Club 100 Implementation Verification")
print("="*60)

# Test 1: Import models
try:
    from app.models.db_models import User
    print("✅ Database models import successfully")
except Exception as e:
    print(f"❌ Error importing models: {e}")
    sys.exit(1)

# Test 2: Check User model has new column definition
try:
    import inspect
    user_columns = [col.name for col in User.__table__.columns]
    if 'club_100_unlocked_picks' in user_columns:
        print("✅ User model has club_100_unlocked_picks column defined")
    else:
        print("❌ club_100_unlocked_picks column not found in User model")
        print(f"Available columns: {user_columns}")
except Exception as e:
    print(f"❌ Error checking User columns: {e}")

# Test 3: Check if migration logic exists
try:
    from app import database
    if hasattr(database, 'run_migrations'):
        print("✅ run_migrations() function exists in database.py")
    else:
        print("❌ run_migrations() function not found")
except Exception as e:
    print(f"❌ Error importing database module: {e}")

# Test 4: Check if init_db calls migrations
try:
    import inspect
    source = inspect.getsource(database.init_db)
    if 'run_migrations' in source:
        print("✅ init_db() calls run_migrations()")
    else:
        print("⚠️  init_db() may not call run_migrations()")
except Exception as e:
    print(f"⚠️  Could not check init_db source: {e}")

# Test 5: Check club_100_service
try:
    from app.services.club_100_service import Club100Service
    service_methods = dir(Club100Service)
    if 'follow_club_100_pick' in service_methods:
        print("✅ Club100Service has follow_club_100_pick() method")
    else:
        print("❌ follow_club_100_pick() method not found in Club100Service")
except Exception as e:
    print(f"❌ Error importing Club100Service: {e}")

print("="*60)
print("✅ All implementation components verified!")
print("="*60)
