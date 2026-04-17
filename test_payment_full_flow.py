#!/usr/bin/env python
"""Test full payment flow in Docker"""
import requests
import json
import time

BASE_URL = 'http://localhost:8000/api'

def register():
    """Register a test user"""
    url = f'{BASE_URL}/auth/register/'
    email = f'test_payment_{int(time.time())}@example.com'
    password = 'TestPassword123!'
    username = f'testuser_{int(time.time())}'
    
    payload = {
        'email': email,
        'password': password,
        'username': username
    }
    response = requests.post(url, json=payload)
    print(f'✓ Register: {response.status_code}')
    # Return tuple of (response_data, email, password)
    return response.json(), email, password

def login(email, password):
    """Login user"""
    url = f'{BASE_URL}/auth/login/'
    payload = {'email': email, 'password': password}
    response = requests.post(url, json=payload)
    print(f'✓ Login: {response.status_code}')
    return response.json()

def create_payment_intent(token, amount=9900):
    """Create payment intent"""
    url = f'{BASE_URL}/payment/create-payment-intent'
    headers = {'Authorization': f'Bearer {token}'}
    payload = {'amount': amount, 'currency': 'usd'}
    response = requests.post(url, json=payload, headers=headers)
    print(f'✓ Payment Intent: {response.status_code}')
    if response.status_code != 200:
        print(f'  Response: {response.text[:200]}')
    return response

# Run tests
print('\n=== Testing Payment Flow ===\n')
try:
    # 1. Register
    user_resp, email, password = register()
    print(f'Registered user email: {email}')
    
    # 2. Login
    login_resp = login(email, password)
    token = login_resp.get('access_token')
    if not token:
        print(f'❌ Failed to get access token: {login_resp}')
        exit(1)
    
    # 3. Create payment intent
    payment_resp = create_payment_intent(token)
    if payment_resp.status_code == 200:
        print(f'\n✅ SUCCESS! Payment endpoint working!')
        print(f'\nResponse:\n{json.dumps(payment_resp.json(), indent=2)}')
    else:
        print(f'\n❌ Payment failed with status {payment_resp.status_code}')
        print(f'Response:\n{payment_resp.text}')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
