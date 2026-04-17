import httpx
import asyncio

async def test():
    base = 'http://localhost:8000/api'
    async with httpx.AsyncClient() as client:
        # Test login first
        print('Testing login...')
        r = await client.post(base + '/auth/login', json={'email': 'test@example.com', 'password': 'password123'})
        print(f'Login status: {r.status_code}')
        
        if r.status_code == 200:
            token = r.json().get('access_token')
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test predictions
            print('\nTesting predictions...')
            r = await client.get(base + '/predictions/?sport=soccer_epl&limit=2', headers=headers, timeout=130)
            print(f'Predictions status: {r.status_code}')
            
            if r.status_code == 200:
                data = r.json()
                print(f'Received {len(data)} predictions')
                if data:
                    print('\nFirst prediction:')
                    print(f"  Matchup: {data[0].get('matchup')}")
                    print(f"  Prediction: {data[0].get('prediction')}")
                    print(f"  Confidence: {data[0].get('confidence')}%")
                    print(f"  Type: {type(data[0].get('prediction'))}")
                    print('\n✓ SUCCESS! Predictions are now working!')
            else:
                print(f'Error: {r.text[:500]}')
        else:
            print(f'Login failed: {r.text}')

asyncio.run(test())
