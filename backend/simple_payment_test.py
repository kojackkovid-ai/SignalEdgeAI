#!/usr/bin/env python
import httpx
import json
import sys

try:
    # Login first
    resp = httpx.post(
        "http://localhost:8000/api/auth/login/",
        json={"email": "payment4@test.com", "password": "Test123!@"},
        timeout=30.0
    )
    
    if resp.status_code == 200:
        token = resp.json()["access_token"]
        
        # Make payment request
        resp = httpx.post(
            "http://localhost:8000/api/payment/create-payment-intent",
            headers={"Authorization": f"Bearer {token}"},
            json={"plan": "pro", "billing_cycle": "monthly"},
            timeout=30.0
        )
        
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Detail: {data.get('detail', 'No detail')}")
        
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
