#!/usr/bin/env python3
"""
Test auth endpoints after fixing DB connection
"""
import sys
import os
import asyncio
import random
import string

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_auth():
    print("\n" + "=" * 80)
    print("TESTING AUTH ENDPOINTS (Login/Register)")
    print("=" * 80)
    
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        
        # Generate unique test user
        random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        test_email = f"auth_test_{random_id}@example.com"
        test_password = "TestPassword123!@"
        test_username = f"testuser_{random_id}"
        
        client = TestClient(app)
        
        print(f"\n[TEST 1] Register new user...")
        print(f"  Email: {test_email}")
        print(f"  Username: {test_username}")
        
        # Try to register
        register_response = client.post(
            "/api/auth/register/",
            json={
                "email": test_email,
                "password": test_password,
                "username": test_username
            }
        )
        
        if register_response.status_code == 200:
            print(f"  ✓✓✓ REGISTRATION SUCCESSFUL ✓✓✓")
            data = register_response.json()
            token = data.get("access_token")
            print(f"      Auth token: {token[:30] if token else 'None'}...")
        else:
            print(f"  ✗ Registration failed: {register_response.status_code}")
            print(f"      Response: {register_response.json()}")
            return False
        
        # Test login
        print(f"\n[TEST 2] Login with registered user...")
        
        login_response = client.post(
            "/api/auth/login/",
            json={
                "email": test_email,
                "password": test_password
            }
        )
        
        if login_response.status_code == 200:
            print(f"  ✓✓✓ LOGIN SUCCESSFUL ✓✓✓")
            data = login_response.json()
            token = data.get("access_token")
            print(f"      Auth token: {token[:30] if token else 'None'}...")
            return True
        else:
            print(f"  ✗ Login failed: {login_response.status_code}")
            print(f"      Response: {login_response.json()}")
            return False
            
    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_auth())
    
    print("\n" + "=" * 80)
    if success:
        print("✓✓✓ AUTH SYSTEM IS WORKING ✓✓✓")
        print("  - Registration works")
        print("  - Login works")
        print("  - Database connection is fixed")
        print("  - You can now use the app normally")
    else:
        print("✗ Auth system still has issues")
    print("=" * 80 + "\n")
    
    sys.exit(0 if success else 1)
