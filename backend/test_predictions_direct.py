import asyncio
import sys
sys.path.insert(0, '.')

async def test_predictions_endpoint():
    """Test the predictions endpoint directly"""
    from app.services.prediction_service import PredictionService
    from app.models.db_models import User
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    print("=== Testing Predictions Service ===")
    
    # Test getting predictions
    service = PredictionService()
    
    # Use a mock user for testing
    class MockUser:
        id = "test-user-id"
        subscription_tier = "starter"
    
    # Test predictions for different sports
    sports_to_test = [
        ("basketball_nba", "NBA"),
        ("icehockey_nhl", "NHL"),
        ("baseball_mlb", "MLB"),
        ("americanfootball_nfl", "NFL"),
    ]
    
    for sport_key, sport_name in sports_to_test:
        print(f"\n--- Testing {sport_name} ({sport_key}) ---")
        try:
            # Note: This would need a real DB session to work
            print(f"  Sport: {sport_name}")
            print(f"  The service should return predictions for this sport")
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n=== Testing Player Props API ===")
    from app.services.espn_prediction_service import ESPNPredictionService
    espn_service = ESPNPredictionService()
    
    # Test NBA props
    print("\n--- Testing NBA Player Props ---")
    try:
        props = await espn_service.get_player_props('basketball_nba', '401810707')
        print(f"Got {len(props)} NBA player props")
        if props:
            sample = props[0]
            print(f"Sample prop keys: {list(sample.keys())}")
            print(f"Sample prop: {sample.get('player', 'N/A')} - {sample.get('prediction', 'N/A')}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test_predictions_endpoint())
