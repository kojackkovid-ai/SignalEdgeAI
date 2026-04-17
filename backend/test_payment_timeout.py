import httpx
import json
import sys

print("Testing payment endpoint with longer timeout...")

try:
    # Register a test user with longer timeout
    print("\n1. Registering user...")  
    register_resp = httpx.post(
        "http://localhost:8000/api/auth/register/",
        json={
            "email": "paymenttest3@test.com",
            "password": "Test123!@",
            "username": "paymenttest3"
        },
        timeout=30.0
    )
    
    print(f"   Status: {register_resp.status_code}")
    if register_resp.status_code not in [200, 201, 409]:
        print(f"   Response: {register_resp.text[:200]}")
        sys.exit(1)
    
    # Login
    print("\n2. Logging in...")
    login_resp = httpx.post(
        "http://localhost:8000/api/auth/login/",
        json={
            "email": "paymenttest3@test.com",
            "password": "Test123!@"
        },
        timeout=30.0
    )
    
    print(f"   Status: {login_resp.status_code}")
    if login_resp.status_code == 200:
        token = login_resp.json()["access_token"]
        print(f"   ✅ Token obtained")
        
        # Try payment
        print("\n3. Creating payment intent...")
        payment_resp = httpx.post(
            "http://localhost:8000/api/payment/create-payment-intent",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "plan": "pro",
                "billing_cycle": "monthly"
            },
            timeout=30.0
        )
        
        print(f"   Status: {payment_resp.status_code}")
        resp_json = payment_resp.json()
        print(f"   Response: {json.dumps(resp_json, indent=2)}")
        
        if payment_resp.status_code == 200:
            print("\n✅ SUCCESS! Payment endpoint working!")
            print(f"Client Secret: {resp_json['client_secret'][:50]}...")
        else:
            print(f"\n❌ Payment error: {resp_json.get('detail', 'Unknown')}")
    else:
        print(f"   ❌ Login failed: {login_resp.text[:200]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
