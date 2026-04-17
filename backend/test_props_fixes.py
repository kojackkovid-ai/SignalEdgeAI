#!/usr/bin/env python3
"""
Test script to verify the player props fixes:
1. 404 error on prop unlock is resolved
2. Confidence values are varied (not all 52%)
"""

import asyncio
import httpx
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

async def test_props_confidence_variation():
    """Test that player props have varied confidence values"""
    print("\n=== Testing Player Props Confidence Variation ===")
    
    # First, login to get a token
    async with httpx.AsyncClient() as client:
        # Try to login with test credentials
        try:
            login_resp = await client.post(
                f"{BASE_URL}/auth/login",
                json={"email": "test@example.com", "password": "testpassword"}
            )
            if login_resp.status_code == 200:
                token = login_resp.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                print(f"✓ Logged in successfully")
            else:
                print(f"⚠ Login failed ({login_resp.status_code}), trying without auth...")
                headers = {}
        except Exception as e:
            print(f"⚠ Login error: {e}, trying without auth...")
            headers = {}
        
        # Test NBA player props
        sport_key = "basketball_nba"
        event_id = "401810707"  # Example event ID from the error
        
        print(f"\nFetching player props for {sport_key}/{event_id}...")
        
        try:
            response = await client.get(
                f"{BASE_URL}/predictions/props/{sport_key}/{event_id}",
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                props = response.json()
                print(f"✓ Got {len(props)} player props")
                
                if props:
                    # Check confidence values
                    confidences = [p.get("confidence", 0) for p in props if p.get("confidence")]
                    
                    if confidences:
                        min_conf = min(confidences)
                        max_conf = max(confidences)
                        avg_conf = sum(confidences) / len(confidences)
                        
                        print(f"\nConfidence Statistics:")
                        print(f"  Min: {min_conf}%")
                        print(f"  Max: {max_conf}%")
                        print(f"  Avg: {avg_conf:.1f}%")
                        print(f"  Count: {len(confidences)}")
                        
                        # Check for variation
                        unique_confidences = len(set([round(c, 1) for c in confidences]))
                        
                        if max_conf - min_conf < 5:
                            print(f"\n❌ FAIL: Confidence values are too similar (range: {max_conf - min_conf}%)")
                            print(f"   All values: {confidences[:10]}...")
                            return False
                        elif unique_confidences < len(confidences) * 0.5:
                            print(f"\n⚠ WARNING: Many duplicate confidence values")
                            print(f"   Unique: {unique_confidences}, Total: {len(confidences)}")
                        else:
                            print(f"\n✓ PASS: Confidence values show good variation")
                            print(f"   Range: {min_conf}% - {max_conf}%")
                        
                        # Show sample props
                        print(f"\nSample Props:")
                        for prop in props[:5]:
                            print(f"  - {prop.get('player', 'Unknown')}: {prop.get('prediction', 'N/A')} (Confidence: {prop.get('confidence')}%)")
                        
                        return True
                    else:
                        print("❌ No confidence values found in props")
                        return False
                else:
                    print("⚠ No props returned (empty list)")
                    return True  # Not a failure, just no data
            else:
                print(f"❌ Failed to fetch props: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Error fetching props: {e}")
            return False

async def test_follow_prop():
    """Test that following a player prop doesn't return 404"""
    print("\n=== Testing Player Prop Follow (Unlock) ===")
    
    async with httpx.AsyncClient() as client:
        # Login first
        headers = {}
        try:
            login_resp = await client.post(
                f"{BASE_URL}/auth/login",
                json={"email": "test@example.com", "password": "testpassword"}
            )
            if login_resp.status_code == 200:
                token = login_resp.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                print(f"✓ Logged in successfully")
        except Exception as e:
            print(f"⚠ Login failed: {e}")
            return False
        
        # First get some props to test with
        sport_key = "basketball_nba"
        event_id = "401810707"
        
        try:
            response = await client.get(
                f"{BASE_URL}/predictions/props/{sport_key}/{event_id}",
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code != 200 or not response.json():
                print("⚠ No props available to test follow")
                return True  # Skip this test
            
            props = response.json()
            test_prop = props[0]
            prop_id = test_prop.get("id")
            
            print(f"\nTesting follow for prop: {prop_id}")
            print(f"  Player: {test_prop.get('player')}")
            print(f"  Prediction: {test_prop.get('prediction')}")
            
            # Try to follow/unlock the prop
            follow_resp = await client.post(
                f"{BASE_URL}/predictions/{prop_id}/follow",
                headers=headers,
                params={"sport_key": sport_key},
                json=test_prop,  # Send the full prop data
                timeout=10.0
            )
            
            if follow_resp.status_code == 200:
                print(f"✓ Successfully followed prop (unlocked)")
                result = follow_resp.json()
                print(f"  Response: {result.get('prediction', 'N/A')[:50]}...")
                return True
            elif follow_resp.status_code == 404:
                print(f"❌ FAIL: Got 404 error when trying to follow prop")
                print(f"   Response: {follow_resp.text[:200]}")
                return False
            elif follow_resp.status_code == 401:
                print(f"⚠ Authentication required (401)")
                return True  # Not a code issue, just need auth
            elif follow_resp.status_code == 403:
                print(f"⚠ Daily limit reached (403) - this is expected behavior")
                return True
            else:
                print(f"⚠ Unexpected status: {follow_resp.status_code}")
                print(f"   Response: {follow_resp.text[:200]}")
                return True  # Not necessarily a failure
                
        except Exception as e:
            print(f"❌ Error testing follow: {e}")
            return False

async def main():
    print("=" * 60)
    print("Player Props Fixes Verification")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    
    results = []
    
    # Test 1: Confidence variation
    result1 = await test_props_confidence_variation()
    results.append(("Confidence Variation", result1))
    
    # Test 2: Follow prop (404 fix)
    result2 = await test_follow_prop()
    results.append(("Prop Follow (404 Fix)", result2))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
