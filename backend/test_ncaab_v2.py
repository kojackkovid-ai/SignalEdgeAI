#!/usr/bin/env python3
"""
Test NCAAB v2 models with VotingClassifier
"""
import asyncio
import sys
from pathlib import Path

# Add paths
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent / "ml-models"))

from app.services.enhanced_ml_service import EnhancedMLService

async def test_ncaab_v2():
    print("=" * 60)
    print("Testing NCAAB v2 Models (VotingClassifier)")
    print("=" * 60)
    
    service = EnhancedMLService()
    
    # Test loading NCAAB moneyline model
    print("\n1. Testing basketball_ncaa_moneyline...")
    result = await service._load_models('basketball_ncaa_moneyline')
    print(f"   Loaded: {result}")
    
    if result:
        print(f"   Models in service: {list(service.models.keys())}")
        
        # Test prediction
        print("\n2. Testing prediction...")
        game_data = {
            'home_team': 'Duke Blue Devils',
            'away_team': 'North Carolina Tar Heels',
            'home_wins': 20,
            'home_losses': 5,
            'away_wins': 18,
            'away_losses': 7,
            'home_recent_wins': 4,
            'away_recent_wins': 3
        }
        
        result = await service.predict('basketball_ncaa', 'moneyline', game_data)
        print(f"\n   Prediction Result:")
        print(f"   - Status: {result.get('status')}")
        print(f"   - Prediction: {result.get('prediction')}")
        print(f"   - Confidence: {result.get('confidence')}%")
        print(f"   - Model Key: {result.get('model_key')}")
        print(f"   - Is Fallback: {result.get('is_fallback', False)}")
        
        if result.get('status') == 'success' and not result.get('is_fallback'):
            print("\n   ✓ SUCCESS: Using real ML model for NCAAB predictions!")
        else:
            print("\n   ✗ WARNING: Still using fallback predictions")
    
    # Test spread model
    print("\n3. Testing basketball_ncaa_spread...")
    result = await service._load_models('basketball_ncaa_spread')
    print(f"   Loaded: {result}")
    
    # Test total model
    print("\n4. Testing basketball_ncaa_total...")
    result = await service._load_models('basketball_ncaa_total')
    print(f"   Loaded: {result}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_ncaab_v2())
