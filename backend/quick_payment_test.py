#!/usr/bin/env python
import httpx
import json

resp = httpx.post(
    "http://localhost:8000/api/auth/login/",
    json={"email": "payment4@test.com", "password": "Test123!@"},
    timeout=30.0
)

if resp.status_code == 200:
    token = resp.json()["access_token"]
    resp = httpx.post(
        "http://localhost:8000/api/payment/create-payment-intent",
        headers={"Authorization": f"Bearer {token}"},
        json={"plan": "pro", "billing_cycle": "monthly"},
        timeout=30.0
    )
    
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
