import requests

def main():
    login_url = 'https://signaledge-ai.fly.dev/api/auth/login'
    login_payload = {
        'email': 'test+flycheck@example.com',
        'password': 'P@ssw0rd123'
    }
    print('=== LOGIN TEST ===')
    r = requests.post(login_url, json=login_payload)
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text}')

    print('\n=== CLUB 100 DATA TEST ===')
    club100_url = 'https://signaledge-ai.fly.dev/api/predictions/club-100-data'
    headers = {
        'Authorization': f'Bearer {r.json()["access_token"]}'
    }
    r2 = requests.get(club100_url, headers=headers)
    print(f'Status: {r2.status_code}')
    print(f'Response keys: {list(r2.json().keys())}' if r2.status_code == 200 else f'Error: {r2.text}')
    if r2.status_code == 200:
        for sport_key in r2.json():
            print(f'  {sport_key}: {len(r2.json()[sport_key])} players')

if __name__ == '__main__':
    main()
