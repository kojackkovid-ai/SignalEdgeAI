#!/usr/bin/env python3
"""
Diagnostic script to find startup issues
"""
import sys
import time

print("Starting diagnostics...")
sys.stdout.flush()

try:
    print("Step 1: Importing settings...")
    sys.stdout.flush()
    from app.config import settings
    print("  OK - Settings imported")
    sys.stdout.flush()
    
    print("Step 2: Importing database...")
    sys.stdout.flush()
    from app.database import engine, get_db
    print("  OK - Database imported")
    sys.stdout.flush()
    
    print("Step 3: Importing models...")
    sys.stdout.flush()
    from app.models import db_models
    print("  OK - Models imported")
    sys.stdout.flush()
    
    print("Step 4: Importing services...")
    sys.stdout.flush()
    from app.services import espn_prediction_service
    print("  OK - Services imported")
    sys.stdout.flush()
    
    print("Step 5: Importing main app...")
    sys.stdout.flush()
    from app.main import app
    print("  OK - Main app imported")
    sys.stdout.flush()
    
    print("\nAll imports successful!")
    
except ImportError as e:
    print(f"  IMPORT ERROR: {e}")
    sys.stdout.flush()
    import traceback
    traceback.print_exc()
    sys.exit(1)
    
except RuntimeError as e:
    print(f"  RUNTIME ERROR: {e}")
    sys.stdout.flush()
    import traceback
    traceback.print_exc()
    sys.exit(1)
    
except Exception as e:
    print(f"  ERROR: {type(e).__name__}: {e}")
    sys.stdout.flush()
    import traceback
    traceback.print_exc()
    sys.exit(1)
