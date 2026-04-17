#!/usr/bin/env python3
"""
Test predictions API to verify models are working
"""
import asyncio
import httpx
from datetime import datetime

async def test_predictions():
    # Use timestamp to create unique email
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f"testuser_{timestamp}@example.com"
    username = f"testuser_{timestamp}"
    
    async with httpx.AsyncClient() as client:
        # Register user first
        register_resp = await client.post('http://localhost:8000/api/auth/register', json={
            'email': email,
            'password': 'password123',
            'username': username
        })
        print(f'Register status: {register_resp.status_code}')
        if register_resp.status_code != 200:
            print(f'Register error: {register_resp.text}')
        
        # Login
        login_resp = await client.post('http://localhost:8000/api/auth/login', json={
            'email': email,
            'password': 'password123'
        })
        print(f'Login status: {login_resp.status_code}')
        
        if login_resp.status_code == 200:
            token = login_resp.json()['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test predictions endpoint
            pred_resp = await client.get('http://localhost:8000/api/predictions/', headers=headers)
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
                else:
                    print('\n❌ No predictions returned - models may not be generating predictions')
            else:
                print(f'Error: {pred_resp.text}')
        else:
            print(f'Login failed: {login_resp.text}')

if __name__ == "__main__":
    asyncio.run(test_predictions())
