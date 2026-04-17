



import requests
import time
import sys

BASE_URL = 'http://localhost:8000'
TOKEN = None

def test_endpoint(name, method, url, **kwargs):
    try:
        print(f'\n=== Testing: {name} ===')
        if method == 'GET':
            r = requests.get(url, timeout=kwargs.get('timeout', 10), headers=kwargs.get('headers', {}))
        else:
            r = requests.post(url, timeout=kwargs.get('timeout', 10), headers=kwargs.get('headers', {}), json=kwargs.get('json', {}))
        
        print(f'Status: {r.status_code}')
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and 'predictions' in data:
                print(f'Predictions count: {len(data["predictions"])}')
            elif isinstance(data, list):
                print(f'Response list count: {len(data)}')
            else:
                print(f'Response keys: {list(data.keys()) if isinstance(data, dict) else "N/A"}')
            return True
        else:
            print(f'Error: {r.text[:200]}')
            return False
    except Exception as e:
        print(f'Exception: {e}')
        return False

def main():
    global TOKEN
    
    # 1. Login first
    print('=== Step 1: Login ===')
    r = requests.post(f'{BASE_URL}/api/auth/login', json={'email': 'testuser12345@example.com', 'password': 'testpass123'}, timeout=10)
    if r.status_code == 200:
        TOKEN = r.json()['access_token']
        print(f'Login successful, token: {TOKEN[:30]}...')
    else:
        print('Login failed')
        sys.exit(1)

    headers = {'Authorization': f'Bearer {TOKEN}'}

    # 2. Test /followed endpoint (the one I fixed)
    test_endpoint('GET /followed (fixed endpoint)', 'GET', f'{BASE_URL}/api/predictions/followed', headers=headers, timeout=30)

    # 3. Test sport filter - NBA
    test_endpoint('GET /predictions?sport=NBA', 'GET', f'{BASE_URL}/api/predictions/?sport=NBA', headers=headers, timeout=60)

    # 4. Test sport filter - NFL
    test_endpoint('GET /predictions?sport=NFL', 'GET', f'{BASE_URL}/api/predictions/?sport=NFL', headers=headers, timeout=60)

    # 5. Test public predictions (no auth)
    test_endpoint('GET /public (no auth)', 'GET', f'{BASE_URL}/api/predictions/public', timeout=10)

    # 6. Test error - no auth header
    print('\n=== Testing: Error handling (no auth) ===')
    r = requests.get(f'{BASE_URL}/api/predictions/', timeout=5)
    print(f'Status (no auth): {r.status_code} (expected 401)')

    # 7. Test error - invalid token
    print('\n=== Testing: Error handling (invalid token) ===')
    r = requests.get(f'{BASE_URL}/api/predictions/', headers={'Authorization': 'Bearer invalid_token'}, timeout=5)
    print(f'Status (invalid token): {r.status_code} (expected 401)')

    print('\n=== API Endpoint Testing Complete ===')

if __name__ == '__main__':
    main()
