import httpx
import asyncio
import sys

async def test_predictions():
    base = 'http://localhost:8000/api'
    
    print("=" * 60)
    print("TESTING PREDICTIONS API")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Step 1: Register a test user
        print("\n1. Registering test user...")
        try:
            r = await client.post(base + '/auth/register', json={
                'email': 'testuser123@example.com',
                'password': 'password123',
                'username': 'testuser123'
            }, timeout=30)
            print(f"   Register status: {r.status_code}")
            if r.status_code == 200:
                print("   ✓ User registered successfully")
            elif r.status_code == 400 and 'already exists' in r.text:
                print("   ℹ User already exists (OK)")
            else:
                print(f"   ⚠ Register response: {r.text[:200]}")
        except Exception as e:
            print(f"   ✗ Register error: {e}")
        
        # Step 2: Login
        print("\n2. Logging in...")
        token = None
        try:
            r = await client.post(base + '/auth/login', json={
                'email': 'testuser123@example.com',
                'password': 'password123'
            }, timeout=30)
            print(f"   Login status: {r.status_code}")
            
            if r.status_code == 200:
                data = r.json()
                token = data.get('access_token')
                print(f"   ✓ Login successful")
                print(f"   ✓ Token received: {token[:20]}...")
            else:
                print(f"   ✗ Login failed: {r.text[:200]}")
                return
        except Exception as e:
            print(f"   ✗ Login error: {e}")
            return
        
        if not token:
            print("\n✗ Cannot proceed without token")
            return
        
        headers = {'Authorization': f'Bearer {token}'}
        
        # Step 3: Test predictions endpoint
        print("\n3. Fetching predictions (NBA)...")
        print("   This may take up to 120 seconds due to ML processing...")
        
        try:
            r = await client.get(
                base + '/predictions/?sport=basketball_nba&limit=2', 
                headers=headers, 
                timeout=130
            )
            print(f"   Predictions status: {r.status_code}")
            
            if r.status_code == 200:
                predictions = r.json()
                print(f"   ✓ Received {len(predictions)} predictions")
                
                if predictions:
                    print("\n   First prediction details:")
                    pred = predictions[0]
                    print(f"   - ID: {pred.get('id')}")
                    print(f"   - Matchup: {pred.get('matchup')}")
                    print(f"   - Sport: {pred.get('sport')}")
                    print(f"   - Prediction: {pred.get('prediction')}")
                    print(f"   - Confidence: {pred.get('confidence')}%")
                    print(f"   - Type: {type(pred.get('prediction'))}")
                    
                    # Verify structure
                    required_fields = ['id', 'sport', 'matchup', 'prediction', 'confidence']
                    missing = [f for f in required_fields if f not in pred]
                    if missing:
                        print(f"   ⚠ Missing fields: {missing}")
                    else:
                        print("   ✓ All required fields present")
                    
                    # Check if prediction is a string (not numpy array)
                    if isinstance(pred.get('prediction'), str):
                        print("   ✓ Prediction is properly formatted as string")
                    else:
                        print(f"   ⚠ Prediction type issue: {type(pred.get('prediction'))}")
                    
                    print("\n" + "=" * 60)
                    print("✓ SUCCESS! Predictions are working correctly!")
                    print("=" * 60)
                    return True
                else:
                    print("   ⚠ No predictions returned (empty array)")
                    print("   This may be due to no upcoming games or ESPN API issues")
            else:
                print(f"   ✗ Error: {r.text[:500]}")
                
        except httpx.TimeoutException:
            print("   ✗ Request timed out (120s)")
            print("   The ML prediction generation is taking too long")
        except Exception as e:
            print(f"   ✗ Error: {e}")
    
    return False

if __name__ == "__main__":
    result = asyncio.run(test_predictions())
    sys.exit(0 if result else 1)
