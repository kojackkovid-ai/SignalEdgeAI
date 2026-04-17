#!/usr/bin/env python3
"""
Test script to verify player props are working correctly after the fix.
"""
import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.espn_prediction_service import ESPNPredictionService

async def test_player_props():
    """Test player props generation for different sports"""
    service = ESPNPredictionService()
    
    print("=" * 80)
    print("TESTING PLAYER PROPS FIX")
    print("=" * 80)
    
    # Test cases with real event IDs from ESPN
    test_cases = [
        ("basketball_nba", "401705956"),  # NBA game
        ("icehockey_nhl", "401459420"),     # NHL game
        ("soccer_epl", "12345"),            # Soccer (may not exist, tests fallback)
    ]
    
    for sport_key, event_id in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing {sport_key} - Event ID: {event_id}")
        print(f"{'='*60}")
        
        try:
            props = await service.get_player_props(sport_key, event_id)
            
            if props:
                print(f"✅ SUCCESS: Generated {len(props)} player props")
                
                # Show first few props
                for i, prop in enumerate(props[:3]):
                    print(f"\n  Prop {i+1}:")
                    print(f"    - Player: {prop.get('player', 'N/A')}")
                    print(f"    - Market: {prop.get('market_key', 'N/A')}")
                    print(f"    - Prediction: {prop.get('prediction', 'N/A')}")
                    print(f"    - Confidence: {prop.get('confidence', 'N/A')}%")
            else:
                print(f"❌ FAILED: No props returned (should have mock props as fallback)")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}")
    
    await service.close()

if __name__ == "__main__":
    asyncio.run(test_player_props())
