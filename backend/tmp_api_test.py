import requests
from app.services.auth_service import AuthService

# Use an existing user id from database
user_id = '2a6ec753-cb97-4e82-8d2d-5a5c3773b0a6'  # pro user

service = AuthService()
# Create token with subject
token = service.create_access_token({'sub': user_id})
print('token:', token)

headers = {'Authorization': f'Bearer {token}'}
url = 'http://127.0.0.1:8000/api/predictions?sport=basketball_nba&limit=5'
resp = requests.get(url, headers=headers, timeout=30)
print('status', resp.status_code)
print('resp keys', resp.json().keys())
print('predictions count', len(resp.json().get('predictions', [])))
if resp.json().get('predictions'):
    print('sample', resp.json()['predictions'][0])
