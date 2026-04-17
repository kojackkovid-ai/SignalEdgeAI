#!/usr/bin/env python
"""
Minimal payment test that writes output to file for debugging
"""
import httpx
import json
import sys
import os

# Write output to file
output_file = "payment_test_output.txt"
with open(output_file, "w") as f:
    f.write("Starting payment test...\n")
    
    try:
        # Test 1: Register
        f.write("1. Registering user...\n")
        resp = httpx.post(
            "http://localhost:8000/api/auth/register/",
            json={
                "email": "payment4@test.com",
                "password": "Test123!@",
                "username": "payment4"
            },
            timeout=30.0
        )
        f.write(f"   Status: {resp.status_code}\n")
        
        # Test 2: Login
        f.write("2. Logging in...\n")
        resp = httpx.post(
            "http://localhost:8000/api/auth/login/",
            json={
                "email": "payment4@test.com",
                "password": "Test123!@"
            },
            timeout=30.0
        )
        f.write(f"   Status: {resp.status_code}\n")
        
        if resp.status_code == 200:
            token = resp.json()["access_token"]
            f.write(f"   Token obtained\n")
            
            # Test 3: Payment
            f.write("3. Creating payment intent...\n")
            resp = httpx.post(
                "http://localhost:8000/api/payment/create-payment-intent",
                headers={"Authorization": f"Bearer {token}"},
                json={"plan": "pro", "billing_cycle": "monthly"},
                timeout=30.0
            )
            
            f.write(f"   Status: {resp.status_code}\n")
            f.write(f"   Response: {json.dumps(resp.json(), indent=2)}\n")
            
            if resp.status_code == 200:
                f.write("✅ SUCCESS!\n")
            else:
                f.write(f"❌ Payment failed: {resp.json().get('detail')}\n")
        else:
            f.write(f"   ❌ Login failed\n")
            
    except Exception as e:
        f.write(f"ERROR: {e}\n")

# Print the output file
print(open(output_file).read())
