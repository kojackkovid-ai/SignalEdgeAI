#!/usr/bin/env python3
"""
Staging Deployment Smoke Tests
Tests all critical functionality after deployment to staging
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Tuple

class StagingSmokeTests:
    """Comprehensive smoke tests for staging deployment"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8001"):
        self.base_url = base_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "passed": 0,
            "failed": 0,
            "warnings": 0
        }
    
    def test(self, name: str, method: str = "GET", endpoint: str = "", 
             expected_status: int = 200, payload: Dict = None) -> bool:
        """Run a single test"""
        url = f"{self.base_url}{endpoint}"
        result = {
            "name": name,
            "endpoint": endpoint,
            "method": method,
            "timestamp": datetime.now().isoformat(),
            "passed": False,
            "status_code": None,
            "error": None,
            "response_time_ms": None
        }
        
        try:
            start = time.time()
            
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=payload, timeout=10)
            else:
                response = requests.request(method, url, json=payload, timeout=10)
            
            elapsed = (time.time() - start) * 1000
            result["response_time_ms"] = round(elapsed, 2)
            result["status_code"] = response.status_code
            
            if response.status_code == expected_status:
                result["passed"] = True
                self.results["passed"] += 1
                status = "✓"
            else:
                result["error"] = f"Expected {expected_status}, got {response.status_code}"
                self.results["failed"] += 1
                status = "✗"
            
            print(f"  {status} {name} ({result['response_time_ms']}ms)")
            
        except requests.exceptions.ConnectionError as e:
            result["error"] = "Connection failed - backend not responding"
            self.results["failed"] += 1
            print(f"  ✗ {name} - Backend not ready")
            
        except requests.exceptions.Timeout:
            result["error"] = "Request timeout"
            self.results["failed"] += 1
            print(f"  ✗ {name} - Timeout")
            
        except Exception as e:
            result["error"] = str(e)
            self.results["failed"] += 1
            print(f"  ✗ {name} - {str(e)}")
        
        self.results["tests"].append(result)
        return result["passed"]
    
    def run_all_tests(self):
        """Run complete smoke test suite"""
        print("\n" + "="*60)
        print("STAGING DEPLOYMENT SMOKE TESTS")
        print("="*60)
        
        # Health checks
        print("\n[HEALTH CHECKS]")
        self.test("Backend health", "GET", "/health", 200)
        self.test("Database connection", "GET", "/api/health/db", 200)
        self.test("Redis connection", "GET", "/api/health/redis", 200)
        
        # Analytics endpoints
        print("\n[ANALYTICS ENDPOINTS]")
        self.test("Accuracy metrics", "GET", "/api/analytics/accuracy", 200)
        self.test("By-sport breakdown", "GET", "/api/analytics/by-sport", 200)
        self.test("Accuracy history", "GET", "/api/analytics/history?days=30", 200)
        self.test("Analytics dashboard", "GET", "/api/analytics/dashboard", 200)
        
        # Prediction endpoints
        print("\n[PREDICTION ENDPOINTS]")
        self.test("List predictions", "GET", "/api/predictions?sport=nba", 200)
        self.test("Get single prediction", "GET", "/api/predictions?limit=1", 200)
        
        # API performance
        print("\n[PERFORMANCE TESTS]")
        start = time.time()
        self.test("Accuracy metrics (perf)", "GET", "/api/analytics/accuracy", 200)
        elapsed = (time.time() - start) * 1000
        
        if elapsed > 5000:
            print(f"  ⚠ WARNING: Analytics endpoint took {elapsed:.0f}ms (>5s threshold)")
            self.results["warnings"] += 1
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        total = self.results["passed"] + self.results["failed"]
        if total == 0:
            print("⚠ No tests run - backend not responding")
            return False
        
        print(f"Passed: {self.results['passed']}/{total}")
        print(f"Failed: {self.results['failed']}/{total}")
        print(f"Warnings: {self.results['warnings']}")
        
        if self.results["failed"] == 0:
            print("\n✓ STAGING READY FOR 24-HOUR TESTING")
            return True
        else:
            print(f"\n✗ {self.results['failed']} tests failed - staging not ready")
            return False
    
    def save_results(self):
        """Save test results"""
        output = f"staging_smoke_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults saved to: {output}")
        return output


def main():
    """Run smoke tests"""
    print("Starting staging smoke tests...")
    print("Waiting for backend to be ready...")
    
    # Wait for backend
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://127.0.0.1:8001/health", timeout=2)
            if response.status_code == 200:
                print("✓ Backend ready!")
                break
        except:
            if attempt % 5 == 0:
                print(f"  Attempt {attempt+1}/{max_attempts}...")
            time.sleep(1)
    else:
        print("✗ Backend failed to start within timeout")
        return 1
    
    # Run tests
    suite = StagingSmokeTests()
    success = suite.run_all_tests()
    suite.save_results()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
