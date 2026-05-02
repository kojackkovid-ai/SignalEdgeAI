import requests

def main():
    url = 'https://signaledge-ai.fly.dev/api/auth/register'
    payload = {
        'email': 'test+flycheck@example.com',
        'password': 'P@ssw0rd123',
        'username': 'flycheck'
    }
    r = requests.post(url, json=payload)
    print(r.status_code)
    print(r.headers)
    print(r.text)

if __name__ == '__main__':
    main()
