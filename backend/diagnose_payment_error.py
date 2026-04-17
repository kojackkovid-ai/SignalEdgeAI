#!/usr/bin/env python3
"""
Minimal test to identify the exact error from the payment endpoint
"""
import sys
import os
import asyncio
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test():
    print("\n" + "=" * 70)
    print("PAYMENT ENDPOINT ERROR DIAGNOSIS")
    print("=" * 70)
    
    try:
        # Test 1: Check imports
        print("\n1. Checking imports...")
        try:
            from app.main import app
            print("   ✓ app imported successfully")
        except Exception as e:
            print(f"   ✗ Failed to import app: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Test 2: Check payment router
        print("\n2. Checking payment router...")
        from app.routes import payment
        print(f"   ✓ Payment router imported")
        print(f"      create_payment_intent function exists: {hasattr(payment, 'create_payment_intent')}")
        
        # Test 3: Create test client
        print("\n3. Creating FastAPI test client...")
        from fastapi.testclient import TestClient
        client = TestClient(app)
        print("   ✓ Test client created")
        
        # Test 4: Try endpoint without auth (should fail with 401)
        print("\n4. Testing endpoint WITHOUT auth (expecting 401)...")
        response = client.post(
            "/api/payment/create-payment-intent",
            json={
                "plan": "pro",
                "billing_cycle": "monthly"
            }
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        if response.status_code == 401:
            print("   ✓ Correctly requires authentication")
        
        # Test 5: Create user and get token
        print("\n5. Creating test user...")
        signup_response = client.post(
            "/api/auth/signup",
            json={
                "email": "payment_test_123@example.com",
                "password": "TestPass123!@",
                "confirm_password": "TestPass123!@",
                "first_name": "Test",
                "last_name": "User"
            }
        )
        print(f"   Signup Status: {signup_response.status_code}")
        
        token = None
        if signup_response.status_code == 200:
            print("   ✓ User created successfully")
            token = signup_response.json().get("access_token")
        elif signup_response.status_code == 400:
            # User might already exist, try login
            print("   ! User might exist, trying login...")
            login_response = client.post(
                "/api/auth/login",
                json={
                    "email": "payment_test_123@example.com",
                    "password": "TestPass123!@"
                }
            )
            print(f"   Login Status: {login_response.status_code}")
            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                print("   ✓ User logged in, got token")
            else:
                print(f"   ✗ Login failed: {login_response.json()}")
        else:
            print(f"   ✗ Signup failed: {signup_response.json()}")
        
        if not token:
            print("\n   ✗ Could not get auth token")
            return
        
        # Test 6: Call endpoint WITH auth
        print(f"\n6. Testing endpoint WITH auth token...")
        print(f"   Token: {token[:30]}...")
        
        payment_response = client.post(
            "/api/payment/create-payment-intent",
            json={
                "plan": "pro",
                "billing_cycle": "monthly"
            },
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        
        print(f"   Status: {payment_response.status_code}")
        response_json = payment_response.json()
        print(f"   Response:")
        print(f"   {json.dumps(response_json, indent=2)}")
        
        if payment_response.status_code == 200:
            print("\n   ✓✓✓ PAYMENT ENDPOINT WORKS! ✓✓✓")
        else:
            print(f"\n   ✗ Payment endpoint returned {payment_response.status_code}")
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
