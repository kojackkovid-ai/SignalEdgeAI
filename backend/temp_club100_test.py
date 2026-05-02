import json
import urllib.request
import urllib.error

base = 'https://signaledge-ai.fly.dev/api/predictions'

print('=== GET Club 100 Data ===')
try:
    with urllib.request.urlopen(f'{base}/club-100/data') as r:
        body = r.read().decode('utf-8')
        print('status:', r.status)
        print(json.dumps(json.loads(body), indent=2)[:2000])
except urllib.error.HTTPError as e:
    print('HTTPError', e.code, e.reason)
    print(e.read().decode('utf-8', errors='ignore'))
except Exception as e:
    print('Error', e)

print('\n=== POST Club 100 Unlock (no auth) ===')
req = urllib.request.Request(f'{base}/club-100/unlock', method='POST')
try:
    with urllib.request.urlopen(req) as r:
        print('status:', r.status)
        print(r.read().decode('utf-8', errors='ignore'))
except urllib.error.HTTPError as e:
    print('HTTPError', e.code, e.reason)
    print(e.read().decode('utf-8', errors='ignore'))
except Exception as e:
    print('Error', e)

print('\n=== POST Club 100 Follow (no auth) ===')
player_id = 'test-player-123'
req = urllib.request.Request(f'{base}/club-100/follow/{player_id}', method='POST')
try:
    with urllib.request.urlopen(req) as r:
        print('status:', r.status)
        print(r.read().decode('utf-8', errors='ignore'))
except urllib.error.HTTPError as e:
    print('HTTPError', e.code, e.reason)
    print(e.read().decode('utf-8', errors='ignore'))
except Exception as e:
    print('Error', e)
