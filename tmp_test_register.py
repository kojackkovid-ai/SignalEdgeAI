import requests
url = 'https://signaledge-ai.fly.dev/api/auth/register'
payload = {'email': 'debug+register2@example.com', 'password': 'Password123', 'username': 'debuguser2'}
r = requests.post(url, json=payload, timeout=20)
print(r.status_code)
print(r.text)
