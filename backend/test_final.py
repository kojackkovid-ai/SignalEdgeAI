#!/usr/bin/env python3
"""
Final API test - no Unicode
"""
import asyncio
import httpx
import sys

async def test_api():
    """Test API endpoints"""
    results = []
    
    async with httpx.AsyncClient() as client:
        # Test 1: Health check
        print("=== TEST 1: Health Check ===")
        try:
            resp = await client.get('http://localhost:8000/health', timeout=10)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"  API Status: {data.get('status', 'unknown')}")
                print("PASS: Health check working")
                results.append(("Health", True))
            else:
                print(f"FAIL: Status {resp.status_code}")
                results.append(("Health", False))
        except Exception as e:
            print(f"FAIL: {e}")
            results.append(("Health", False))
        
        print()
        
        # Test 2: Public predictions
        print("=== TEST 2: Public Predictions ===")
        try:
            resp = await client.get('http://localhost:8000/api/predictions/public', timeout=30)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    print(f"Found {len(data)} public predictions")
                    if len(data) > 0:
                        pred = data[0]
                        print(f"  Sport: {pred.get('sport', 'N/A')}")
                        print(f"  Matchup: {pred.get('matchup', 'N/A')}")
                        conf = pred.get('confidence', 0)
                        print(f"  Confidence: {conf}%")
                        print("PASS: Public predictions working")
                        results.append(("Public Predictions", True))
                    else:
                        print("WARN: No predictions (may be no games today)")
                        results.append(("Public Predictions", True))
                else:
                    print(f"FAIL: Unexpected format: {type(data)}")
                    results.append(("Public Predictions", False))
            else:
                print(f"FAIL: Status {resp.status_code}")
                print(f"  Response: {resp.text[:200]}")
                results.append(("Public Predictions", False))
        except Exception as e:
            print(f"FAIL: {e}")
            results.append(("Public Predictions", False))
        
        print()
        
        # Test 3: Check ML models loaded
        print("=== TEST 3: ML Model Status ===")
        try:
            resp = await client.get('http://localhost:8000/ready', timeout=10)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                checks = data.get('checks', {})
                ml_ready = checks.get('ml_service', False)
                if ml_ready:
                    print("PASS: ML service is ready")
                    results.append(("ML Models", True))
                else:
                    print(f"WARN: ML service not ready")
                    results.append(("ML Models", False))
            else:
                print(f"FAIL: Status {resp.status_code}")
                results.append(("ML Models", False))
        except Exception as e:
            print(f"FAIL: {e}")
            results.append(("ML Models", False))
    
    # Summary
    print()
    print("=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(test_api())
    sys.exit(0 if success else 1)
