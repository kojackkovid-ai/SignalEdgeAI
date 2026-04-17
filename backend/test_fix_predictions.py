#!/usr/bin/env python3
"""
Quick test to verify predictions API response format
"""
import asyncio
import httpx
from datetime import datetime

async def test_predictions_format():
    """Test that predictions endpoint returns correct format"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f"testuser_{timestamp}@example.com"
    username = f"testuser_{timestamp}"
    
    async with httpx.AsyncClient() as client:
        # Register user
        register_resp = await client.post('http://localhost:8000/api/auth/register', json={
            'email': email,
            'password': 'password123',
            'username': username
        })
        print(f'Register status: {register_resp.status_code}')
        
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
            pred_resp = await client.get('http://localhost:8000/api/predictions/?sport=basketball_nba&limit=5', headers=headers)
            print(f'\nPredictions status: {pred_resp.status_code}')
            
            if pred_resp.status_code == 200:
                data = pred_resp.json()
                print(f'Response type: {type(data)}')
                print(f'Response keys: {list(data.keys()) if isinstance(data, dict) else "N/A (array)"}')
                
                # Check format
                if isinstance(data, dict) and 'predictions' in data:
                    predictions = data['predictions']
                    print(f'✅ CORRECT FORMAT: Found "predictions" key with {len(predictions)} items')
                    if predictions:
                        print(f'Sample prediction: {predictions[0].get("matchup", "N/A")}')
                    return True
                elif isinstance(data, list):
                    print(f'⚠️  OLD FORMAT: Direct array with {len(data)} items')
                    print('   Backend needs to be restarted to apply the fix')
                    return False
                else:
                    print(f'❌ UNEXPECTED FORMAT: {data}')
                    return False
            else:
                print(f'Error: {pred_resp.text}')
                return False
        else:
            print(f'Login failed: {login_resp.text}')
            return False

if __name__ == "__main__":
    result = asyncio.run(test_predictions_format())
    if result:
        print('\n✅ TEST PASSED: Predictions API returns correct format')
    else:
        print('\n❌ TEST FAILED: Predictions API format issue detected')
