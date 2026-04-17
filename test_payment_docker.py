#!/usr/bin/env python
"""
Test payment endpoint after Docker redeploy
"""
import httpx
import json

print("Testing payment endpoint after Docker redeploy...\n")

try:
    # Register a new test user
    print("1. Registering test user...")
    reg_resp = httpx.post(
        "http://localhost:8000/api/auth/register/",
        json={
            "email": "docker-test@test.com",
            "password": "Test123!@",
            "username": "dockertest"
        },
        timeout=30.0
    )
    print(f"   Status: {reg_resp.status_code}")
    
    # Login
    print("2. Logging in...")
    login_resp = httpx.post(
        "http://localhost:8000/api/auth/login/",
        json={"email": "docker-test@test.com", "password": "Test123!@"},
        timeout=30.0
    )
    print(f"   Status: {login_resp.status_code}")
    
    if login_resp.status_code == 200:
        token = login_resp.json()["access_token"]
        print("   ✅ Logged in successfully")
        
        # Test payment endpoint
        print("\n3. Testing payment endpoint...")
        payment_resp = httpx.post(
            "http://localhost:8000/api/payment/create-payment-intent",
            headers={"Authorization": f"Bearer {token}"},
            json={"plan": "pro", "billing_cycle": "monthly"},
            timeout=30.0
        )
        
        print(f"   Status: {payment_resp.status_code}")
        data = payment_resp.json()
        
        if payment_resp.status_code == 200:
            print("\n✅ SUCCESS! Payment endpoint is working!")
            print(f"   Payment Intent ID: {data.get('payment_intent_id')}")
            print(f"   Amount: ${data.get('amount', 0) / 100:.2f}")
        else:
            print(f"\n❌ Payment failed: {data.get('detail', 'Unknown error')}")
            print(f"   Full response: {json.dumps(data, indent=2)}")
    else:
        print(f"❌ Login failed: {login_resp.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")
