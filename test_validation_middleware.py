#!/usr/bin/env python3
"""
Test Validation Middleware with Invalid Data
Tests the Pydantic validation and middleware with various invalid inputs
"""

import asyncio
import aiohttp
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

async def test_validation_middleware():
    """Test validation middleware with invalid data"""

    base_url = "http://localhost:8080"  # Adjust if running on different port

    test_cases = [
        {
            "name": "Invalid email format",
            "endpoint": "/api/auth/register",
            "method": "POST",
            "data": {
                "email": "invalid-email",
                "password": "testpass123",
                "subscription_tier": "starter"
            },
            "expected_status": 422
        },
        {
            "name": "Missing required field",
            "endpoint": "/api/auth/register",
            "method": "POST",
            "data": {
                "email": "test@example.com",
                "password": "testpass123"
                # Missing subscription_tier
            },
            "expected_status": 422
        },
        {
            "name": "Invalid subscription tier",
            "endpoint": "/api/auth/register",
            "method": "POST",
            "data": {
                "email": "test@example.com",
                "password": "testpass123",
                "subscription_tier": "invalid_tier"
            },
            "expected_status": 422
        },
        {
            "name": "Oversized payload",
            "endpoint": "/api/auth/register",
            "method": "POST",
            "data": {
                "email": "test@example.com",
                "password": "testpass123",
                "subscription_tier": "starter",
                "large_field": "x" * (10 * 1024 * 1024)  # 10MB string
            },
            "expected_status": 413
        },
        {
            "name": "Invalid JSON",
            "endpoint": "/api/auth/register",
            "method": "POST",
            "data": "invalid json {",
            "expected_status": 422
        },
        {
            "name": "SQL injection attempt",
            "endpoint": "/api/auth/login",
            "method": "POST",
            "data": {
                "email": "admin' OR '1'='1",
                "password": "password"
            },
            "expected_status": 422
        }
    ]

    async with aiohttp.ClientSession() as session:
        print("🧪 Testing Validation Middleware with Invalid Data")
        print("=" * 60)

        passed = 0
        total = len(test_cases)

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['name']}")
            print(f"   Endpoint: {test_case['endpoint']}")
            print(f"   Expected Status: {test_case['expected_status']}")

            try:
                # Prepare request
                url = f"{base_url}{test_case['endpoint']}"
                headers = {"Content-Type": "application/json"}

                if test_case["method"] == "POST":
                    if isinstance(test_case["data"], str):
                        # Invalid JSON case
                        async with session.post(url, data=test_case["data"], headers=headers) as response:
                            status = response.status
                            try:
                                response_data = await response.json()
                            except:
                                response_data = await response.text()
                    else:
                        async with session.post(url, json=test_case["data"], headers=headers) as response:
                            status = response.status
                            try:
                                response_data = await response.json()
                            except:
                                response_data = await response.text()
                else:
                    async with session.get(url) as response:
                        status = response.status
                        try:
                            response_data = await response.json()
                        except:
                            response_data = await response.text()

                # Check result
                if status == test_case["expected_status"]:
                    print(f"   ✅ PASS - Got expected status {status}")
                    passed += 1
                else:
                    print(f"   ❌ FAIL - Expected {test_case['expected_status']}, got {status}")
                    print(f"   Response: {response_data}")

            except aiohttp.ClientError as e:
                print(f"   ❌ ERROR - Connection failed: {e}")
            except Exception as e:
                print(f"   ❌ ERROR - Unexpected error: {e}")

        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All validation tests passed!")
            return True
        else:
            print("⚠️  Some validation tests failed. Check middleware implementation.")
            return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_validation_middleware())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)