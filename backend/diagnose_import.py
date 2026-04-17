#!/usr/bin/env python
"""Diagnose where the import hangs"""
import sys
import traceback

print("1. Testing config import...")
try:
    from app.config import settings
    print("   ✅ Config imported")
except Exception as e:
    print(f"   ❌ Config import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("2. Testing database import...")
try:
    from app.database import init_db, AsyncSessionLocal
    print("   ✅ Database imported")
except Exception as e:
    print(f"   ❌ Database import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("3. Testing models import...")
try:
    from app.models.db_models import User
    print("   ✅ Models imported")
except Exception as e:
    print(f"   ❌ Models import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("4. Testing logger setup...")
try:
    from app.utils.structured_logging import setup_structured_logging, get_logger
    setup_structured_logging()
    logger = get_logger(__name__)
    print("   ✅ Logger initialized")
except Exception as e:
    print(f"   ❌ Logger setup failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("5. Testing FastAPI import...")
try:
    from fastapi import FastAPI
    app = FastAPI()
    print("   ✅ FastAPI app created")
except Exception as e:
    print(f"   ❌ FastAPI import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("6. Testing routes import...")
try:
    from app.routes import predictions, auth, users
    print("   ✅ Routes imported")
except Exception as e:
    print(f"   ❌ Routes import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("7. Testing MAIN APP import (if this hangs, something in app.main.py is blocking)...")
try:
    from app.main import app as main_app
    print("   ✅ Main app imported successfully")
except Exception as e:
    print(f"   ❌ Main app import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n✅ All imports successful!")

