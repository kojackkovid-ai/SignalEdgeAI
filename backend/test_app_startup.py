#!/usr/bin/env python
"""Test if app starts without errors"""
import sys
import asyncio

sys.path.insert(0, '.')

async def test():
    try:
        print("1. Testing imports...")
        from app.main import app
        print("✅ App imported successfully")
        
        print("\n2. Testing auth service...")
        from app.services.auth_service import AuthService
        auth = AuthService()
        print("✅ AuthService initialized")
        
        print("\n3. Testing database...")
        from app.database import get_db
        print("✅ Database module imported")
        
        print("\n4. Checking routes...")
        for route in app.routes:
            if hasattr(route, 'path') and 'auth' in route.path:
                print(f"   - {route.methods} {route.path}")
        
        print("\n✅ ALL CHECKS PASSED")
        print("\nApp should be ready to start with:")
        print("  python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

asyncio.run(test())
