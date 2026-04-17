#!/usr/bin/env python3
"""
Synchronous test of predictions API
"""
import requests
from datetime import datetime

def test_predictions():
    # Use timestamp to create unique email
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f"testuser_{timestamp}@example.com"
    username = f"testuser_{timestamp}"
    
    # Register user first
    register_resp = requests.post('http://localhost:8000/api/auth/register', json={
        'email': email,
        'password': 'password123',
        'username': username
    }, timeout=30)
    print(f'Register status: {register_resp.status_code}')
    if register_resp.status_code != 200:
        print(f'Register error: {register_resp.text}')
    
    # Login
    login_resp = requests.post('http://localhost:8000/api/auth/login', json={
        'email': email,
        'password': 'password123'
    }, timeout=30)
    print(f'Login status: {login_resp.status_code}')
    
    if login_resp.status_code == 200:
        token = login_resp.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test predictions endpoint with longer timeout
        print('Fetching predictions (this may take 30-60 seconds)...')
        pred_resp = requests.get('http://localhost:8000/api/predictions/', headers=headers, timeout=120)
        print(f'Predictions status: {pred_resp.status_code}')
        if pred_resp.status_code == 200:
            data = pred_resp.json()
            print(f'Number of predictions: {len(data) if isinstance(data, list) else 0}')
            if data and len(data) > 0:
                print(f'Sample prediction keys: {list(data[0].keys())}')
                print(f'Sample prediction sport: {data[0].get("sport")}')
                print(f'Sample prediction matchup: {data[0].get("matchup")}')
                print(f'Sample prediction confidence: {data[0].get("confidence")}')
                print(f'Sample prediction prediction: {data[0].get("prediction")}')
                print('\n✅ PREDICTIONS ARE NOW SHOWING!')
                return True
            else:
                print('\n❌ No predictions returned - models may not be generating predictions')
                return False
        else:
            print(f'Error: {pred_resp.text}')
            return False
    else:
        print(f'Login failed: {login_resp.text}')
        return False

if __name__ == "__main__":
    success = test_predictions()
    exit(0 if success else 1)
