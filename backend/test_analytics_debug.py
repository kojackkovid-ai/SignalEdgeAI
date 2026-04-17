#!/usr/bin/env python
"""Test prediction creation and analytics querying"""
import asyncio
import sys
import os
import requests

# Write output to file for debugging
output_file = open("test_output_debug.txt", "w")

def log(msg):
    print(msg)
    output_file.write(msg + "\n")
    output_file.flush()

# Test 1: Create a prediction via API
print("=" * 60)
print("TEST 1: Creating a prediction via API...")
print("=" * 60)

try:
    # Create a test user first
    login_response = requests.post(
        "http://127.0.0.1:8000/auth/register",
        json={"username": "analyticstest", "email": "analyticstest@test.com", "password": "testpass123"},
        timeout=5
    )
    print(f"Register response: {login_response.status_code}")
    if login_response.status_code == 200:
        user_data = login_response.json()
        token = user_data.get("access_token")
        print(f"Got token")
        
        # Create a prediction
        headers = {"Authorization": f"Bearer {token}"}
        pred_response = requests.post(
            "http://127.0.0.1:8000/predictions/create",
            json={
                "sport": "basketball",
                "league": "nba",
                "matchup": "Team A vs Team B",
                "prediction": "Over 210",
                "confidence": 0.75,
                "prediction_type": "over_under",
                "sport_key": "basketball_nba",
                "reasoning": ["Test"],
                "model_weights": {}
            },
            headers=headers,
            timeout=5
        )
        print(f"Prediction create response: {pred_response.status_code}")
        if pred_response.status_code == 200:
            print(f"Prediction created successfully")
        else:
            print(f"Error: {pred_response.text}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Query analytics endpoint
print("\n" + "=" * 60)
print("TEST 2: Querying analytics endpoint...")
print("=" * 60)

try:
    analytics_response = requests.get(
        "http://127.0.0.1:8000/api/analytics/accuracy?days=90",
        timeout=10
    )
    print(f"Analytics response status: {analytics_response.status_code}")
    data = analytics_response.json()
    print(f"Total predictions: {data.get('total_predictions')}")
    print(f"Resolved predictions: {data.get('resolved_predictions')}")
    print(f"Win rate: {data.get('win_rate')}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Query database directly
print("\n" + "=" * 60)
print("TEST 3: Querying database directly...")
print("=" * 60)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def query_db():
    from app.database import AsyncSessionLocal
    from app.models.db_models import Prediction
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        stmt = select(Prediction)
        result = await session.execute(stmt)
        predictions = result.scalars().all()
        print(f"Direct DB query: {len(predictions)} total predictions")
        
        stmt = select(Prediction).filter(Prediction.resolved_at.isnot(None))
        result = await session.execute(stmt)
        resolved = result.scalars().all()
        print(f"Direct DB query: {len(resolved)} resolved predictions")

try:
    asyncio.run(query_db())
except Exception as e:
    print(f"Error: {e}")

print("\nTest completed")
