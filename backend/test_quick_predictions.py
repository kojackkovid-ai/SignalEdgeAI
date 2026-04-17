#!/usr/bin/env python3
"""
Quick test to verify predictions are working
"""
import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_predictions():
    print("="*70)
    print("QUICK PREDICTIONS API TEST")
    print("="*70)
    
    # Test health endpoint first
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"\n1. Health Check: {resp.status_code}")
        if resp.status_code == 200:
            print("   ✓ Server is running")
        else:
            print(f"   ✗ Health check failed: {resp.text[:100]}")
            return False
    except Exception as e:
        print(f"\n1. Health Check: FAILED")
        print(f"   ✗ Error: {e}")
        print("\n   Is the server running? Start it with: python -m uvicorn app.main:app --reload")
        return False
    
    # Test predictions endpoint without auth (public endpoint)
    sports = ["basketball_nba", "soccer_epl", "icehockey_nhl"]
    
    for sport in sports:
        try:
            print(f"\n2. Testing {sport} predictions...")
            resp = requests.get(
                f"{BASE_URL}/api/predictions/?sport={sport}&limit=2",
                timeout=30
            )
            print(f"   Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                predictions = data.get("predictions", [])
                print(f"   ✓ Got {len(predictions)} predictions")
                
                if predictions:
                    p = predictions[0]
                    print(f"   Sample: {p.get('matchup', 'N/A')}")
                    print(f"   Confidence: {p.get('confidence', 'N/A')}%")
            else:
                print(f"   ✗ Error: {resp.text[:200]}")
                
        except Exception as e:
            print(f"   ✗ Exception: {e}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    return True

if __name__ == "__main__":
    success = test_predictions()
    sys.exit(0 if success else 1)
