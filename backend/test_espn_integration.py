#!/usr/bin/env python3
"""
Test script to verify ESPN API integration is working correctly
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.services.espn_prediction_service import ESPNPredictionService

async def test_espn_integration():
    """Test ESPN API integration"""
    print("🚀 Testing ESPN API Integration...")
    
    service = ESPNPredictionService()
    
    try:
        # Test 1: Get NBA predictions
        print("\n📊 Testing NBA predictions...")
        nba_predictions = await service.get_predictions("basketball_nba")
        print(f"✅ Found {len(nba_predictions)} NBA predictions")
        
        if nba_predictions:
            pred = nba_predictions[0]
            print(f"   Sample: {pred['matchup']} - {pred['prediction']} ({pred['confidence']}%)")
            print(f"   Reasoning factors: {len(pred.get('reasoning', []))}")
        
        # Test 2: Get NHL predictions  
        print("\n🏒 Testing NHL predictions...")
        nhl_predictions = await service.get_predictions("icehockey_nhl")
        print(f"✅ Found {len(nhl_predictions)} NHL predictions")
        
        # Test 3: Get player props
        if nba_predictions:
            print("\n🏀 Testing NBA player props...")
            event_id = nba_predictions[0]['event_id']
            sport_key = nba_predictions[0]['sport_key']
            
            props = await service.get_player_props(sport_key, event_id)
            print(f"✅ Found {len(props)} player props for {nba_predictions[0]['matchup']}")
            
            if props:
                prop = props[0]
                print(f"   Sample: {prop['player']} - {prop['prediction']} ({prop['confidence']}%)")
                print(f"   Reasoning factors: {len(prop.get('reasoning', []))}")
        
        print(f"\n🎉 ESPN Integration Test Complete!")
        print(f"   Total NBA predictions: {len(nba_predictions)}")
        print(f"   Total NHL predictions: {len(nhl_predictions)}")
        print(f"   Player props available: {'Yes' if 'props' in locals() and len(props) > 0 else 'No'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing ESPN integration: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await service.close()

if __name__ == "__main__":
    success = asyncio.run(test_espn_integration())
    sys.exit(0 if success else 1)