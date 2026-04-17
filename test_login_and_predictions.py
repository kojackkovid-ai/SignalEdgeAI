#!/usr/bin/env python3
"""
Quick test script to verify login flow and real predictions
Run this in the backend directory after starting the server
"""

import httpx
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000/api"
TEST_EMAIL = f"testuser_{int(datetime.now().timestamp())}@test.com"
TEST_PASSWORD = "TestPassword123!"
TEST_USERNAME = "testuser"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'

def print_step(num, msg):
    print(f"\n{Colors.BLUE}Step {num}: {msg}{Colors.END}")

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.YELLOW}ℹ {msg}{Colors.END}")

async def test_registration():
    """Test user registration"""
    print_step(1, "Testing User Registration")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "username": TEST_USERNAME
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            user_id = data.get("user_id")
            tier = data.get("tier")
            print_success(f"Registration successful")
            print_info(f"Email: {TEST_EMAIL}")
            print_info(f"User ID: {user_id}")
            print_info(f"Tier: {tier}")
            print_info(f"Token: {token[:50]}...")
            return token, user_id
        else:
            print_error(f"Registration failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None, None

async def test_login():
    """Test user login"""
    print_step(2, "Testing User Login")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            user_id = data.get("user_id")
            print_success(f"Login successful")
            print_info(f"Token received: {token[:50]}...")
            return token, user_id
        else:
            print_error(f"Login failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None, None

async def test_get_user_profile(token):
    """Test getting user profile"""
    print_step(3, "Testing Get User Profile (/users/me)")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"User profile retrieved")
            print_info(f"Username: {data.get('username')}")
            print_info(f"Email: {data.get('email')}")
            print_info(f"Tier: {data.get('subscription_tier')}")
            return True
        else:
            print_error(f"Get profile failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False

async def test_real_predictions(token):
    """Test getting real predictions"""
    print_step(4, "Testing Real Predictions Endpoint (/predictions)")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/predictions/",
            headers={"Authorization": f"Bearer {token}"},
            params={"limit": 3}
        )
        
        if response.status_code == 200:
            predictions = response.json()
            if predictions:
                print_success(f"Retrieved {len(predictions)} predictions")
                
                for i, pred in enumerate(predictions, 1):
                    print_info(f"\nPrediction {i}:")
                    print(f"  Sport: {pred.get('sport')}")
                    print(f"  League: {pred.get('league')}")
                    print(f"  Matchup: {pred.get('matchup')}")
                    print(f"  Prediction: {pred.get('prediction')}")
                    print(f"  Confidence: {pred.get('confidence')}%")
                    if 'reasoning' in pred:
                        print(f"  Reasoning: {len(pred['reasoning'])} factors")
                return True
            else:
                print_info("No predictions currently available (might be OddsAPI issue)")
                return True
        else:
            print_error(f"Get predictions failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False

async def test_public_predictions():
    """Test public predictions endpoint (no auth)"""
    print_step(5, "Testing Public Predictions Endpoint (no auth)")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/predictions/public",
            params={"limit": 2}
        )
        
        if response.status_code == 200:
            predictions = response.json()
            print_success(f"Public predictions retrieved: {len(predictions)} items")
            return True
        else:
            print_error(f"Public predictions failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False

async def main():
    """Run all tests"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print("Sports Prediction Platform - Login & Predictions Test")
    print(f"{'='*60}{Colors.END}")
    
    # Test registration
    token, user_id = await test_registration()
    if not token:
        print_error("Cannot continue without registration")
        return
    
    # Test login
    login_token, _ = await test_login()
    if not login_token:
        print_error("Cannot continue without login")
        return
    
    # Test user profile
    profile_ok = await test_get_user_profile(login_token)
    
    # Test real predictions
    predictions_ok = await test_real_predictions(login_token)
    
    # Test public predictions
    public_ok = await test_public_predictions()
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}")
    print("Test Summary")
    print(f"{'='*60}{Colors.END}")
    
    if profile_ok and predictions_ok and public_ok:
        print_success("All tests passed! ✨")
        print_info("You should now be able to login in the frontend")
    else:
        print_error("Some tests failed. Check errors above.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
