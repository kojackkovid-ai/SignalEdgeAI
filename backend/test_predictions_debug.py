"""
Debug test for predictions endpoint
"""
import asyncio
import sys
sys.path.insert(0, 'c:/Users/bigba/Desktop/New folder/sports-prediction-platform/backend')

from app.services.espn_prediction_service import ESPNPredictionService

async def test_predictions():
    """Test the get_predictions method directly"""
    service = ESPNPredictionService()
    
    print("Testing get_predictions method...")
    print("=" * 50)
    
    try:
        # Test getting predictions for all sports
        predictions = await service.get_predictions(limit=10)
        print(f"Found {len(predictions)} predictions")
        
        if predictions:
            print("\nSample predictions:")
            for i, pred in enumerate(predictions[:3]):
                matchup = pred.get('matchup', 'N/A')
                prediction = pred.get('prediction', 'N/A')
                confidence = pred.get('confidence', 0)
                print(f"  {i+1}. {matchup} - {prediction} ({confidence}%)")
        else:
            print("No predictions returned")
        
        # Test getting predictions for specific sport
        print("\nTesting NBA predictions...")
        nba_preds = await service.get_predictions(sport="basketball_nba", limit=5)
        print(f"Found {len(nba_preds)} NBA predictions")
        
        if nba_preds:
            for i, pred in enumerate(nba_preds[:2]):
                matchup = pred.get('matchup', 'N/A')
                prediction = pred.get('prediction', 'N/A')
                print(f"  {i+1}. {matchup} - {prediction}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    await service.close()

if __name__ == "__main__":
    asyncio.run(test_predictions())
