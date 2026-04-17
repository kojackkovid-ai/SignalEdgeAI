#!/usr/bin/env python3
"""
Test predictions with very long timeout
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
    
    # Login
    login_resp = requests.post('http://localhost:8000/api/auth/login', json={
        'email': email,
        'password': 'password123'
    }, timeout=30)
    print(f'Login status: {login_resp.status_code}')
    
    if login_resp.status_code == 200:
        token = login_resp.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test predictions endpoint with very long timeout (5 minutes)
        print('Fetching predictions (this may take 2-5 minutes for first call)...')
        try:
            pred_resp = requests.get(
                'http://localhost:8000/api/predictions/', 
                headers=headers, 
                timeout=300  # 5 minutes
            )
            print(f'Predictions status: {pred_resp.status_code}')
            
            if pred_resp.status_code == 200:
                data = pred_resp.json()
                print(f'Number of predictions: {len(data) if isinstance(data, list) else 0}')
                
                if data and len(data) > 0:
                    print(f'\n✅ SUCCESS! Found {len(data)} predictions')
                    print(f'\nFirst prediction:')
                    print(f'  Sport: {data[0].get("sport")}')
                    print(f'  Matchup: {data[0].get("matchup")}')
                    print(f'  Prediction: {data[0].get("prediction")}')
                    print(f'  Confidence: {data[0].get("confidence")}%')
                    return True
                else:
                    print('\n❌ No predictions returned')
                    return False
            else:
                print(f'Error: {pred_resp.text}')
                return False
                
        except requests.exceptions.Timeout:
            print('\n❌ Request timed out even with 5 minute timeout')
            print('The server is taking too long to generate predictions.')
            print('This could be due to:')
            print('  1. ML models not loaded properly')
            print('  2. ESPN API being slow')
            print('  3. Too many games to process')
            return False
        except Exception as e:
            print(f'\n❌ Error: {e}')
            return False
    else:
        print(f'Login failed: {login_resp.text}')
        return False

if __name__ == "__main__":
    success = test_predictions()
    exit(0 if success else 1)
