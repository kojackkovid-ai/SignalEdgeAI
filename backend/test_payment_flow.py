#!/usr/bin/env python3
"""
Simulate the user payment flow to test if endpoints work
"""
import sys
import os
import asyncio
import random
import string

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_full_flow():
    print("\n" + "=" * 80)
    print("SIMULATING FULL USER PAYMENT UPGRADE FLOW")
    print("=" * 80)
    
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        
        # Generate unique test user
        random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        test_email = f"upgrade_test_{random_id}@example.com"
        test_password = "TestPassword123!@"
        test_plan = "pro"
        test_cycle = "monthly"
        
        client = TestClient(app)
        
        print(f"\n[STEP 1] Creating test user: {test_email}")
        print(f"  Plan: {test_plan}, Cycle: {test_cycle}")
        
        # Step 1: Create user
        signup_response = client.post(
            "/api/auth/register/",
            json={
                "email": test_email,
                "password": test_password,
                "username": f"testuser_{random_id}"
            }
        )
        
        auth_token = None
        if signup_response.status_code == 200:
            print(f"  ✓ User created successfully")
            auth_token = signup_response.json().get("access_token")
        else:
            print(f"  ! Signup status: {signup_response.status_code}")
            # Try login if exists
            login_response = client.post(
                "/api/auth/login/",
                json={"email": test_email, "password": test_password}
            )
            if login_response.status_code == 200:
                print(f"  ✓ User logged in successfully")
                auth_token = login_response.json().get("access_token")
            else:
                print(f"  ✗ Could not create/login user: {login_response.json()}")
                return False
        
        if not auth_token:
            print(f"  ✗ No auth token received")
            return False
        
        print(f"  ✓ Auth token: {auth_token[:30]}...")
        
        # Step 2: Create payment intent
        print(f"\n[STEP 2] Creating payment intent for {test_plan} plan...")
        
        payment_intent_response = client.post(
            "/api/payment/create-payment-intent",
            json={
                "plan": test_plan,
                "billing_cycle": test_cycle
            },
            headers={
                "Authorization": f"Bearer {auth_token}"
            }
        )
        
        if payment_intent_response.status_code == 200:
            print(f"  ✓ Payment intent created successfully!")
            
            payment_data = payment_intent_response.json()
            payment_intent_id = payment_data.get("payment_intent_id")
            client_secret = payment_data.get("client_secret")
            amount = payment_data.get("amount")
            
            print(f"    - Payment Intent ID: {payment_intent_id}")
            print(f"    - Amount: ${amount/100:.2f}")
            print(f"    - Client Secret: {client_secret[:50]}...")
            
            print(f"\n[SUCCESS] ✓✓✓")
            print(f"  Payment endpoint is working correctly!")
            print(f"  User can proceed to Stripe payment form")
            return True
        else:
            error_detail = payment_intent_response.json().get("detail", "Unknown error")
            print(f"  ✗ Payment intent creation failed: {payment_intent_response.status_code}")
            print(f"    Error: {error_detail}")
            
            if "Invalid API Key" in error_detail or "sk_test" in error_detail:
                print(f"\n  ISSUE: Stripe API Key problem")
                print(f"  The backend has the correct key, but Stripe is rejecting it")
                print(f"  Possible causes:")
                print(f"    1. Backend not restarted after code changes")
                print(f"    2. Python cache stale (.pyc files)")
                print(f"    3. Wrong Stripe test key in .env")
            elif "User not found" in error_detail:
                print(f"\n  ISSUE: User lookup failed")
                print(f"  Check database connection")
            elif "401" in str(payment_intent_response.status_code):
                print(f"\n  ISSUE: Authentication failed")
                print(f"  Token issue or auth service problem")
            
            return False
            
    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_full_flow())
    
    print("\n" + "=" * 80)
    if success:
        print("✓ PAYMENT FLOW TEST PASSED - User upgrade should work!")
    else:
        print("✗ TEST FAILED - Check issues above")
        print("\nNEXT STEPS:")
        print("  1. Make sure backend is RUNNING (python -m uvicorn app.main:app)")
        print("  2. Verify by running this test again")
    print("=" * 80 + "\n")
    
    sys.exit(0 if success else 1)
