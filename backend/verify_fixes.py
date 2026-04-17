
import asyncio
import logging
from datetime import datetime
from app.services.odds_api_service import OddsApiService
from app.services.ml_service import MLService

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_fixes():
    print("--- Testing ML Service Fixes ---")
    ml_service = MLService()
    
    # Test odds conversion
    print("Testing string odds conversion:")
    odds_str = "-110"
    prob = ml_service.calculate_implied_probability(odds_str)
    print(f"Odds '{odds_str}' -> Prob: {prob:.4f}")
    assert prob > 0.5, "Should handle string odds correctly"
    
    odds_str_plus = "+150"
    prob_plus = ml_service.calculate_implied_probability(odds_str_plus)
    print(f"Odds '{odds_str_plus}' -> Prob: {prob_plus:.4f}")
    assert prob_plus < 0.5, "Should handle positive string odds correctly"

    print("\n--- Testing Odds API Service Fixes ---")
    odds_service = OddsApiService()
    
    # Mock Event Data
    mock_event = {
        "id": "test_event_1",
        "sport_key": "americanfootball_nfl",
        "home_team": "Home Team",
        "away_team": "Away Team",
        "commence_time": "2024-02-04T00:00:00Z", # 7 PM ET on Feb 3
        "bookmakers": [
            {
                "key": "fanduel",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Home Team", "price": -150},
                            {"name": "Away Team", "price": +130}
                        ]
                    },
                    {
                        "key": "spreads",
                        "outcomes": [
                            {"name": "Home Team", "point": -3.5, "price": -110},
                            {"name": "Away Team", "point": 3.5, "price": -110}
                        ]
                    },
                    {
                        "key": "totals",
                        "outcomes": [
                            {"name": "Over", "point": 45.5, "price": -110},
                            {"name": "Under", "point": 45.5, "price": -110}
                        ]
                    }
                ]
            }
        ]
    }
    
    print("Transforming Mock Event...")
    prediction = await odds_service.transform_event_to_prediction(mock_event, "americanfootball_nfl")
    
    if prediction:
        print("\nPrediction Result:")
        print(f"Game Time Display: {prediction['game_time']}")
        print(f"Prediction: {prediction['prediction']}")
        
        print("\nReasoning:")
        found_spread = False
        found_total = False
        for r in prediction['reasoning']:
            print(f"- {r['factor']}: {r['explanation']}")
            if "Spread Line" in r['factor']:
                found_spread = True
            if "Total Line" in r['factor']:
                found_total = True
        
        if "Feb 03" in prediction['game_time']:
            print("\n✅ Date/Time Fix Verified: Correctly converted Feb 4 UTC to Feb 3 ET")
        else:
            print(f"\n❌ Date/Time Fix Failed: Got {prediction['game_time']}")
            
        if found_spread and found_total:
            print("✅ Spread/Total Info Verified: Found in reasoning")
        else:
            print("❌ Spread/Total Info Failed: Missing in reasoning")
    else:
        print("❌ Transformation returned None")

if __name__ == "__main__":
    asyncio.run(test_fixes())
