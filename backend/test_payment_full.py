import httpx
import json

print("Testing payment endpoint...")

# Register a test user
print("\n1. Registering user...")
register_resp = httpx.post(
    "http://localhost:8000/api/auth/register/",
    json={
        "email": "paymenttest2@test.com",
        "password": "Test123!@",
        "username": "paymenttest2"
    }
)

print(f"   Status: {register_resp.status_code}")
if register_resp.status_code not in [200, 201]:
    print(f"   Response: {register_resp.text}")
    if register_resp.status_code == 409:
        print("   User already exists, continuing...")

# Login
print("\n2. Logging in...")
login_resp = httpx.post(
    "http://localhost:8000/api/auth/login/",
    json={
        "email": "paymenttest2@test.com",
        "password": "Test123!@"
    }
)

print(f"   Status: {login_resp.status_code}")
if login_resp.status_code == 200:
    token = login_resp.json()["access_token"]
    print(f"   ✅ Token obtained: {token[:50]}...")
    
    # Try payment
    print("\n3. Creating payment intent...")
    payment_resp = httpx.post(
        "http://localhost:8000/api/payment/create-payment-intent",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "plan": "pro",
            "billing_cycle": "monthly"
        }
    )
    
    print(f"   Status: {payment_resp.status_code}")
    print(f"   Response: {json.dumps(payment_resp.json(), indent=2)}")
else:
    print(f"   ❌ Login failed: {login_resp.text}")
