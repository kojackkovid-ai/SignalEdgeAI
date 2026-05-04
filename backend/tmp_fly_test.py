import json
import urllib.request
import urllib.error
import uuid

base = 'https://signaledge-ai.fly.dev'
email = f'test+{uuid.uuid4().hex[:8]}@example.com'
password = 'TestPass123!'
username = f'testuser_{uuid.uuid4().hex[:8]}'
payload = {'email': email, 'password': password, 'username': username}
register_url = base + '/api/auth/register'

print('Registering with email:', email)

try:
    req = urllib.request.Request(register_url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode('utf-8')
        print('REGISTER STATUS', resp.status)
        print(body)
        token = json.loads(body)['access_token']

    club_url = base + '/api/predictions/club-100/data'
    req2 = urllib.request.Request(club_url, headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req2, timeout=60) as resp2:
        print('CLUB100 STATUS', resp2.status)
        print(resp2.read(2000).decode('utf-8'))
except urllib.error.HTTPError as e:
    print('HTTP ERR', e.code, e.reason)
    try:
        print(e.read().decode('utf-8'))
    except Exception:
        pass
except Exception as e:
    print('ERR', type(e), e)
    import traceback
    traceback.print_exc()
