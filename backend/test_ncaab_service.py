#!/usr/bin/env python3
"""
Test NCAAB model loading in EnhancedMLService
"""
import asyncio
import sys
from pathlib import Path

# Add paths
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent / "ml-models"))

from app.services.enhanced_ml_service import EnhancedMLService

async def test_ncaab_models():
    print("=" * 60)
    print("Testing NCAAB Model Loading in EnhancedMLService")
    print("=" * 60)
    
    service = EnhancedMLService()
    
    # Test loading NCAAB moneyline model
    print("\n1. Testing basketball_ncaa_moneyline...")
    result = await service._load_models('basketball_ncaa_moneyline')
    print(f"   Result: {result}")
    
    # Test loading NCAAB spread model
    print("\n2. Testing basketball_ncaa_spread...")
    result = await service._load_models('basketball_ncaa_spread')
    print(f"   Result: {result}")
    
    # Test loading NCAAB total model
    print("\n3. Testing basketball_ncaa_total...")
    result = await service._load_models('basketball_ncaa_total')
    print(f"   Result: {result}")
    
    # Check loaded models
    print(f"\n4. Loaded models in service:")
    for key in service.models.keys():
        print(f"   - {key}")
    
    # Test prediction if models loaded
    if 'basketball_ncaa_moneyline' in service.models:
        print("\n5. Testing prediction...")
        game_data = {
            "home_team": "Duke Blue Devils",
            "away_team": "North Carolina Tar Heels",
            "home_wins": 20,
            "home_losses": 5,
            "away_wins": 18,
            "away_losses": 7,
            "home_recent_wins": 4,
            "away_recent_wins": 3
        }
        
        result = await service.predict('basketball_ncaa', 'moneyline', game_data)
        print(f"   Prediction result: {result}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_ncaab_models())
