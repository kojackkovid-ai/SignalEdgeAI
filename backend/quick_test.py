import requests
import time
import sys

def test_api():
    print('=== Quick API Test ===')
    
    # Wait for server
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get('http://localhost:8000/health', timeout=2)
            if response.status_code == 200:
                print('✓ Server is running')
                break
        except:
            if i == max_retries - 1:
                print('✗ Server not responding')
                return False
            time.sleep(1)
    
    # Test register
    timestamp = str(int(time.time()))
    email = f'test_{timestamp}@example.com'
    
    print(f'\nRegistering: {email}')
    response = requests.post(
        'http://localhost:8000/api/auth/register',
        json={'email': email, 'password': 'Test123', 'username': f'test_{timestamp}'},
        timeout=5
    )
    print(f'Status: {response.status_code}')
    
    if response.status_code == 200:
        print('✓ Registration successful')
    else:
        print(f'Error: {response.text[:100]}')
        return False
    
    # Test login
    print(f'\nLogging in: {email}')
    response = requests.post(
        'http://localhost:8000/api/auth/login',
        json={'email': email, 'password': 'Test123'},
        timeout=5
    )
    print(f'Status: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        print('✓ Login successful')
        print(f'User ID: {data.get("user_id")}')
        return True
    else:
        print(f'Error: {response.text[:100]}')
        return False

if __name__ == '__main__':
    success = test_api()
    sys.exit(0 if success else 1)
