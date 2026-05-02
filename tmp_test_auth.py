import requests
url = 'https://signaledge-ai.fly.dev/api/auth/login'
payload = {'email': 'debug+test2@example.com', 'password': 'Password123'}
r = requests.post(url, json=payload, timeout=20)
print(r.status_code)
print(r.text)
