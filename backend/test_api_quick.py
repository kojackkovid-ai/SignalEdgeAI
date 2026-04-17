import requests

resp = requests.get('http://localhost:8000/api/predictions?sport=basketball_nba', timeout=30)
print(f'Status: {resp.status_code}')
if resp.status_code == 200:
    data = resp.json()
    print(f'Got {len(data)} predictions')
    if data:
        first = data[0]
        print(f'First prediction confidence: {first.get("confidence")}')
        print(f'First prediction matchup: {first.get("matchup")}')
