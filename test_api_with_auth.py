"""
Test with authentication to properly test the backend API
"""
import asyncio
import httpx
import json

async def test_api_authenticated():
    async with httpx.AsyncClient(timeout=120) as client:
        # First try to register/login or use a known token
        # For development, let's try using the email/password endpoint
        
        login_url = "http://localhost:8000/api/auth/login"
        print(f"Attempting login...")
        
        # Try with a test user
        try:
            login_resp = await client.post(login_url, json={
                "email": "test@example.com",
                "password": "test123"
            })
            print(f"Login status: {login_resp.status_code}")
            
            if login_resp.status_code == 200:
                token_data = login_resp.json()
                token = token_data.get("access_token")
                print(f"✓ Got token: {token[:20]}...")
            else:
                print(f"Login failed: {login_resp.text[:200]}")
                token = None
        except Exception as e:
            print(f"Login error: {e}")
            token = None
        
        # Now try the props endpoint with or without token
        api_url = "http://localhost:8000/api/predictions/game/soccer_usa_mls/761502/full"
        print(f"\nTesting props endpoint: {api_url}")
        
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            resp = await client.get(api_url, headers=headers)
            print(f"Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"\n✓ Response received successfully")
                print(f"\n📊 Props Summary:")
                props_summary = data.get("props_summary", {})
                for key, val in props_summary.items():
                    print(f"  {key}: {val}")
                
                print(f"\n🎯 Goals: {len(data.get('goals', []))} props")
                print(f"🎯 Assists: {len(data.get('assists', []))} props")
                print(f"🎯 Team Props: {len(data.get('team_props', []))} props")
                
                if data.get('goals'):
                    g = data['goals'][0]
                    print(f"\n📝 Sample Goal Prop:")
                    print(f"  Player: {g.get('player')}")
                    print(f"  Prediction: {g.get('prediction')}")
                    print(f"  Season Avg: {g.get('season_avg')}")
                    print(f"  Recent 10: {g.get('recent_10_avg')}")
                
            else:
                print(f"Error: {resp.status_code}")
                print(f"Response: {resp.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_authenticated())
