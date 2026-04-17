#!/usr/bin/env python3
"""
Test Analytics Endpoints
Verifies that all accuracy metrics endpoints are working correctly.
"""

import requests
import json
import time
from datetime import datetime

API_URL = "http://localhost:8000"

def test_endpoint(method: str, endpoint: str, expected_status: int = 200) -> dict:
    """Test an endpoint and return the response."""
    url = f"{API_URL}{endpoint}"
    print(f"\n{'='*70}")
    print(f"Testing: {method} {endpoint}")
    print(f"{'='*70}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == expected_status:
            print("✓ PASS")
            return response.json() if response.text else {}
        else:
            print(f"✗ FAIL - Expected {expected_status}, got {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return {}
            
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return {}


def main():
    """Run all analytics tests."""
    print("\n" + "="*70)
    print("ANALYTICS ENDPOINTS TEST SUITE")
    print("="*70)
    
    # Check if API is running
    try:
        requests.get(f"{API_URL}/health", timeout=5)
        print("✓ Backend API is running")
    except:
        print("✗ Backend API is not running at", API_URL)
        print("  Start it with: python -m uvicorn app.main:app --reload")
        return 1
    
    results = {}
    
    # Test 1: Accuracy Metrics
    print("\n[1/6] Testing Accuracy Metrics Endpoint")
    metrics = test_endpoint("GET", "/api/analytics/accuracy?days=30")
    results['accuracy'] = bool(metrics)
    if metrics:
        print(f"Total predictions: {metrics.get('total_predictions', 'N/A')}")
        print(f"Win rate: {metrics.get('win_rate', 'N/A')}")
        print(f"ROI: {metrics.get('roi', 'N/A')}")
        print(f"Calibration error: {metrics.get('calibration_error', 'N/A')}")
    
    # Test 2: Calibration Data
    print("\n[2/6] Testing Calibration Data Endpoint")
    calibration = test_endpoint("GET", "/api/analytics/calibration?days=30")
    results['calibration'] = bool(calibration)
    if calibration:
        data_points = calibration.get('calibration_data', [])
        print(f"Calibration data points: {len(data_points)}")
        if data_points:
            print(f"First point: confidence={data_points[0].get('confidence')}, actual={data_points[0].get('actual_accuracy')}")
    
    # Test 3: Predictions List
    print("\n[3/6] Testing Predictions List Endpoint")
    predictions = test_endpoint("GET", "/api/analytics/predictions?days=30&limit=5")
    results['predictions'] = bool(predictions)
    if predictions:
        pred_list = predictions.get('predictions', [])
        print(f"Total predictions: {predictions.get('total', 'N/A')}")
        print(f"Returned: {len(pred_list)}")
        if pred_list:
            print(f"First prediction: {pred_list[0].get('sport_key')} - {pred_list[0].get('market_type')}")
    
    # Test 4: Summary
    print("\n[4/6] Testing Summary Endpoint")
    summary = test_endpoint("GET", "/api/analytics/summary")
    results['summary'] = bool(summary)
    if summary:
        for period, data in summary.get('summary', {}).items():
            print(f"{period}: accuracy={data.get('accuracy')}, roi={data.get('roi')}")
    
    # Test 5: Accuracy by Sport Filter
    print("\n[5/6] Testing Accuracy Metrics with Sport Filter")
    sport_metrics = test_endpoint("GET", "/api/analytics/accuracy?days=30&sport_key=basketball_nba")
    results['sport_filter'] = bool(sport_metrics)
    if sport_metrics:
        print(f"NBA accuracy: {sport_metrics.get('win_rate', 'N/A')}")
    
    # Test 6: Accuracy by Market Filter
    print("\n[6/6] Testing Accuracy Metrics with Market Filter")
    market_metrics = test_endpoint("GET", "/api/analytics/accuracy?days=30&market_type=moneyline")
    results['market_filter'] = bool(market_metrics)
    if market_metrics:
        print(f"Moneyline accuracy: {market_metrics.get('win_rate', 'N/A')}")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20} {status}")
    
    print(f"\n{'='*70}")
    print(f"RESULTS: {passed}/{total} tests passed")
    print(f"{'='*70}\n")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
