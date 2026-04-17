#!/usr/bin/env python3
"""
Comprehensive test of payment endpoint functionality
"""
import sys
import os
import asyncio
import random
import string

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_payment_endpoint():
    print("\n" + "=" * 80)
    print("COMPREHENSIVE PAYMENT ENDPOINT TEST")
    print("=" * 80)
    
    try:
        print("\n1. Initializing FastAPI test client...")
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        print("   ✓ Test client created")
        
        # Create random user to avoid conflicts
        random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        test_email = f"payment_test_{random_id}@example.com"
        test_password = "TestPassword123!@"
        
        print(f"\n2. Creating test user: {test_email}")
        
        # Try signup
        signup_response = client.post(
            "/api/auth/signup",
            json={
                "email": test_email,
                "password": test_password,
                "confirm_password": test_password,
                "first_name": "Test",
                "last_name": "Payment"
            }
        )
        
        token = None
        if signup_response.status_code == 200:
            print(f"   ✓ User created successfully")
            token = signup_response.json().get("access_token")
            print(f"   ✓ Auth token obtained: {token[:30] if token else 'NONE'}...")
        elif signup_response.status_code == 400:
            print(f"   ! User signup returned 400 (might exist)")
            print(f"      Response: {signup_response.json()}")
        else:
            print(f"   ! Signup response: {signup_response.status_code}")
            print(f"      {signup_response.json()}")
        
        if not token:
            print(f"\n   ! Signup didn't return token, checking database...")
            # Try to login instead
            login_response = client.post(
                "/api/auth/login",
                json={
                    "email": test_email,
                    "password": test_password
                }
            )
            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                print(f"   ✓ Login successful, got token")
            else:
                print(f"   ✗ Login failed: {login_response.status_code}")
                print(f"      {login_response.json()}")
        
        if not token:
            print(f"\n   ✗ Could not obtain authentication token")
            return False
        
        # Test the payment endpoint
        print(f"\n3. Testing payment/create-payment-intent endpoint...")
        print(f"   Using auth token: {token[:30]}...")
        
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
        
        print(f"   Status Code: {payment_response.status_code}")
        
        if payment_response.status_code == 200:
            data = payment_response.json()
            print(f"   ✓✓✓ PAYMENT ENDPOINT SUCCESSFUL ✓✓✓")
            print(f"\n   Response data:")
            print(f"      - Payment Intent ID: {data.get('payment_intent_id')}")
            print(f"      - Amount: ${data.get('amount', 0) / 100:.2f}")
            print(f"      - Client Secret: {data.get('client_secret', '')[:50]}...")
            return True
        else:
            data = payment_response.json()
            print(f"   ✗ Payment endpoint returned {payment_response.status_code}")
            print(f"\n   Error Response:")
            print(f"      {data}")
            
            # Check if it's an auth error
            if payment_response.status_code == 401:
                print(f"\n   Issue: Authentication failed")
                print(f"      - Token used: {token[:30]}...")
                print(f"      - Check token validity")
            elif payment_response.status_code == 500:
                print(f"\n   Issue: Internal server error")
                print(f"      - Check backend logs for details")
                print(f"      - Could be database connection issue")
                print(f"      - Could be Stripe API error")
            
            return False
        
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_payment_endpoint())
    
    print("\n" + "=" * 80)
    if success:
        print("✓ PAYMENT ENDPOINT IS WORKING CORRECTLY")
    else:
        print("✗ PAYMENT ENDPOINT HAS ISSUES")
    print("=" * 80 + "\n")
    
    sys.exit(0 if success else 1)
