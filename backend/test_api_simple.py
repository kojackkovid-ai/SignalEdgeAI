#!/usr/bin/env python3
"""
Simple API test script without Unicode characters
"""
import asyncio
import httpx
import json
import sys

async def test_api():
    """Test API endpoints"""
    results = []
    
    async with httpx.AsyncClient() as client:
        # Test 1: Health check
        print("=== TEST 1: Health Check ===")
        try:
            resp = await client.get('http://localhost:8000/api/health', timeout=10)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print("PASS: Health check working")
                results.append(("Health", True))
            else:
                print(f"FAIL: {resp.text[:100]}")
                results.append(("Health", False))
        except Exception as e:
            print(f"FAIL: {e}")
            results.append(("Health", False))
        
        print()
        
        # Test 2: NCAAB Predictions
        print("=== TEST 2: NCAAB Predictions ===")
        try:
            resp = await client.get('http://localhost:8000/api/predictions?sport=ncaab', timeout=30)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    print(f"Found {len(data)} NCAAB predictions")
                    if len(data) > 0:
                        pred = data[0]
                        print(f"  Matchup: {pred.get('matchup', 'N/A')}")
                        print(f"  Prediction: {pred.get('prediction', 'N/A')}")
                        conf = pred.get('confidence', 0)
                        print(f"  Confidence: {conf}%")
                        
                        # Check confidence is not fixed at 50%
                        if conf != 50 and conf > 0:
                            print("PASS: Confidence is dynamic (not fixed 50%)")
                        else:
                            print("WARN: Confidence may be fixed or missing")
                        
                        # Check reasoning
                        reasoning = pred.get('reasoning', [])
                        if reasoning and len(reasoning) > 0:
                            print(f"  Reasoning points: {len(reasoning)}")
                            print("PASS: Has reasoning data")
                        else:
                            print("WARN: No reasoning data")
                        
                        results.append(("NCAAB", True))
                    else:
                        print("WARN: No predictions returned (may be no games today)")
                        results.append(("NCAAB", True))  # Still pass if API works
                else:
                    print(f"FAIL: Unexpected format: {type(data)}")
                    results.append(("NCAAB", False))
            else:
                print(f"FAIL: Status {resp.status_code}")
                results.append(("NCAAB", False))
        except Exception as e:
            print(f"FAIL: {e}")
            results.append(("NCAAB", False))
        
        print()
        
        # Test 3: NBA Predictions (for comparison)
        print("=== TEST 3: NBA Predictions ===")
        try:
            resp = await client.get('http://localhost:8000/api/predictions?sport=nba', timeout=30)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    print(f"Found {len(data)} NBA predictions")
                    if len(data) > 0:
                        pred = data[0]
                        conf = pred.get('confidence', 0)
                        print(f"  Confidence: {conf}%")
                        
                        # Compare reasoning with NCAAB
                        reasoning = pred.get('reasoning', [])
                        print(f"  Reasoning points: {len(reasoning)}")
                        print("PASS: NBA predictions working")
                        results.append(("NBA", True))
                    else:
                        print("WARN: No NBA predictions (may be no games)")
                        results.append(("NBA", True))
                else:
                    print(f"FAIL: Unexpected format")
                    results.append(("NBA", False))
            else:
                print(f"FAIL: Status {resp.status_code}")
                results.append(("NBA", False))
        except Exception as e:
            print(f"FAIL: {e}")
            results.append(("NBA", False))
        
        print()
        
        # Test 4: Check model loading
        print("=== TEST 4: ML Model Status ===")
        try:
            resp = await client.get('http://localhost:8000/api/health', timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                ml_status = data.get('components', {}).get('ml_models', {})
                if ml_status.get('status') == 'healthy':
                    print("PASS: ML models loaded and healthy")
                    results.append(("ML Models", True))
                else:
                    print(f"WARN: ML status: {ml_status}")
                    results.append(("ML Models", False))
            else:
                print("FAIL: Could not check health")
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
