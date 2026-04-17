import asyncio
import httpx

async def test_simple():
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test 1: Health check
        try:
            resp = await client.get('http://localhost:8000/health')
            print(f'Health check: {resp.status_code}')
        except Exception as e:
            print(f'Health error: {e}')
        
        # Test 2: Login with existing user
        try:
            resp = await client.post(
                'http://localhost:8000/api/auth/login',
                json={
                    'email': 'testuser12345@example.com',
                    'password': 'testpass123'
                },
                timeout=60.0
            )
            print(f'Login: {resp.status_code}')
            if resp.status_code == 200:
                data = resp.json()
                token = data.get('access_token', 'N/A')
                print(f'Token received: {token[:20]}...')
                return token
            else:
                print(f'Login failed: {resp.text[:200]}')
        except Exception as e:
            print(f'Login error: {e}')
        return None

async def test_predictions(token):
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.get(
                'http://localhost:8000/api/predictions/',
                headers={'Authorization': f'Bearer {token}'},
                timeout=120.0
            )
            print(f'Predictions status: {resp.status_code}')
            if resp.status_code == 200:
                data = resp.json()
                print(f'Response type: {type(data)}')
                print(f'Response keys: {data.keys() if isinstance(data, dict) else "N/A (list)"}')
                if isinstance(data, dict) and 'predictions' in data:
                    print(f'Number of predictions: {len(data["predictions"])}')
                    if data['predictions']:
                        print(f'First prediction: {data["predictions"][0]}')
                elif isinstance(data, list):
                    print(f'Number of predictions (list): {len(data)}')
                    if data:
                        print(f'First prediction: {data[0]}')
                else:
                    print(f'Raw response: {data}')
            else:
                print(f'Predictions failed: {resp.text[:500]}')
        except Exception as e:
            print(f'Predictions error: {e}')

if __name__ == "__main__":
    token = asyncio.run(test_simple())
    print(f'Final token: {token}')
    if token:
        print('\n--- Testing Predictions ---')
        asyncio.run(test_predictions(token))
