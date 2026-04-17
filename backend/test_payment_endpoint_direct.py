#!/usr/bin/env python3
"""Test the payment endpoint directly"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_endpoint():
    print("\n" + "=" * 70)
    print("TESTING PAYMENT ENDPOINT")
    print("=" * 70)
    
    try:
        # Test 1: Check if payment route is properly registered
        print("\n1. Checking payment route registration...")
        from app.main import app
        
        routes = [route.path for route in app.routes]
        payment_routes = [r for r in routes if 'payment' in r.lower()]
        
        if payment_routes:
            print(f"   ✓ Payment routes found:")
            for route in payment_routes:
                print(f"      - {route}")
        else:
            print(f"   ✗ No payment routes found!")
            print(f"   Available routes: {routes}")
            return False
        
        # Test 2: Test the endpoint via TestClient
        print("\n2. Testing endpoint via TestClient...")
        from fastapi.testclient import TestClient
        from app.services.auth_service import AuthService
        
        client = TestClient(app)
        auth_service = AuthService()
        
        # Create a test user first
        test_email = "payment_test@example.com"
        test_password = "TestPassword123!"
        
        print(f"\n3. Creating test user...")
        signup_response = client.post(
            "/api/auth/signup",
            json={
                "email": test_email,
                "password": test_password,
                "confirm_password": test_password,
                "first_name": "Test",
                "last_name": "User"
            }
        )
        
        token = None
        if signup_response.status_code == 200:
            print(f"   ✓ User created")
            token = signup_response.json().get("access_token")
        else:
            # Try to login
            login_response = client.post(
                "/api/auth/login",
                json={
                    "email": test_email,
                    "password": test_password
                }
            )
            if login_response.status_code == 200:
                print(f"   ✓ User logged in")
                token = login_response.json().get("access_token")
            else:
                print(f"   ! Login/signup didn't work, trying without auth...")
        
        # Test 4: Call the endpoint
        print(f"\n4. Testing payment intent creation...")
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            print(f"   Using token: {token[:30]}...")
        else:
            print(f"   ⚠ No auth token available")
        
        payment_response = client.post(
            "/api/payment/create-payment-intent",
            json={
                "plan": "pro",
                "billing_cycle": "monthly"
            },
            headers=headers
        )
        
        print(f"   Status: {payment_response.status_code}")
        print(f"   Response: {payment_response.json()}")
        
        if payment_response.status_code == 200:
            print(f"   ✓ Payment intent created successfully!")
            return True
        else:
            print(f"   ✗ Payment endpoint returned error")
            return False
        
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_endpoint())
    sys.exit(0 if success else 1)
