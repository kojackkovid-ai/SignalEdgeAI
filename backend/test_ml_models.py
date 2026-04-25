#!/usr/bin/env python3
"""
Test ML models loading
"""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.ml_service import MLService

async def test_ml_models():
    print("Testing ML models loading...")

    service = MLService()
    await service.initialize()

    print(f"Models loaded: {list(service.models.keys())}")
    print(f"Weights: {service.weights}")
    print(f"Initialized: {service.is_initialized}")

    # Test prediction
    test_data = {
        "home_team": "Test Home",
        "away_team": "Test Away",
        "bookmakers": [{
            "markets": [{
                "key": "h2h",
                "outcomes": [
                    {"name": "Test Home", "price": -150},
                    {"name": "Test Away", "price": 130}
                ]
            }]
        }]
    }

    prediction = await service.predict_from_odds(test_data)
    if prediction:
        print(f"Test prediction successful: {prediction['prediction']} with {prediction['confidence']}% confidence")
    else:
        print("Test prediction failed")

if __name__ == "__main__":
    asyncio.run(test_ml_models())