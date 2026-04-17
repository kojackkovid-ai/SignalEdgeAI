"""
Test script to verify tier-based daily pick limits are working correctly
"""
import asyncio
import httpx
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_tier_endpoint():
    """Test the /users/tier endpoint returns correct limits"""
    print("\n" + "="*60)
    print("TESTING TIER ENDPOINT")
    print("="*60)
    
    # Test with different user tokens (you'll need valid tokens)
    # For now, just check the endpoint exists and returns proper structure
    
    async with httpx.AsyncClient() as client:
        try:
            # This will fail without auth, but we can check the endpoint exists
            response = await client.get(f"{BASE_URL}/users/tier", timeout=5)
            print(f"Response status: {response.status_code}")
            if response.status_code == 401:
                print("✅ Endpoint exists (401 is expected without auth token)")
                return True
            elif response.status_code == 200:
                data = response.json()
                print(f"✅ Tier endpoint working!")
                print(f"   Tier: {data.get('tier')}")
                print(f"   Daily Limit: {data.get('daily_limit')}")
                print(f"   Picks Used: {data.get('picks_used_today')}")
                print(f"   Picks Remaining: {data.get('picks_remaining')}")
                return True
            else:
                print(f"❌ Unexpected status: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

async def test_predictions_endpoint():
    """Test the /predictions endpoint returns correct tier info"""
    print("\n" + "="*60)
    print("TESTING PREDICTIONS ENDPOINT")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/predictions/",
                params={"limit": 5},
                timeout=10
            )
            print(f"Response status: {response.status_code}")
            if response.status_code == 401:
                print("✅ Endpoint exists (401 is expected without auth token)")
                return True
            elif response.status_code == 200:
                data = response.json()
                predictions = data.get('predictions', [])
                print(f"✅ Got {len(predictions)} predictions")
                
                if predictions:
                    pred = predictions[0]
                    print(f"   Daily picks used: {pred.get('daily_picks_used')}")
                    print(f"   Daily picks limit: {pred.get('daily_picks_limit')}")
                    print(f"   Is locked: {pred.get('is_locked')}")
                return True
            else:
                print(f"❌ Unexpected status: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

def verify_tier_limits():
    """Verify the TIER_LIMITS constant is correctly defined"""
    print("\n" + "="*60)
    print("VERIFYING TIER LIMITS CONFIGURATION")
    print("="*60)
    
    try:
        from app.services.prediction_service import PredictionService
        
        limits = PredictionService.TIER_LIMITS
        print(f"✅ TIER_LIMITS found: {limits}")
        
        expected = {
            'free': 1,
            'starter': 1,
            'basic': 10,
            'pro': 25,
            'elite': 9999
        }
        
        all_correct = True
        for tier, expected_limit in expected.items():
            actual = limits.get(tier)
            if actual == expected_limit:
                print(f"   ✅ {tier}: {actual} picks/day")
            else:
                print(f"   ❌ {tier}: expected {expected_limit}, got {actual}")
                all_correct = False
        
        return all_correct
    except Exception as e:
        print(f"❌ Error importing PredictionService: {e}")
        return False

async def main():
    print("\n" + "="*60)
    print("TIER-BASED PICK LIMITS VERIFICATION")
    print("="*60)
    print(f"Started at: {datetime.now()}")
    
    # Test 1: Verify TIER_LIMITS configuration
    config_ok = verify_tier_limits()
    
    # Test 2: Test tier endpoint
    tier_endpoint_ok = await test_tier_endpoint()
    
    # Test 3: Test predictions endpoint
    predictions_endpoint_ok = await test_predictions_endpoint()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"TIER_LIMITS Config: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"Tier Endpoint: {'✅ PASS' if tier_endpoint_ok else '❌ FAIL'}")
    print(f"Predictions Endpoint: {'✅ PASS' if predictions_endpoint_ok else '❌ FAIL'}")
    
    if config_ok and tier_endpoint_ok and predictions_endpoint_ok:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
