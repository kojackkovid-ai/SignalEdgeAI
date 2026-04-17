#!/usr/bin/env python3
"""
Test script to verify player props only return real ESPN data.
NO mock data, NO fake data, NO placeholders - only real raw ESPN data.
Returns empty list when real data is unavailable.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.espn_prediction_service import ESPNPredictionService

async def test_player_props_real_data():
    """Test that player props only return real ESPN data"""
    service = ESPNPredictionService()
    
    print("=" * 70)
    print("TESTING: Player Props - Real ESPN Data Only")
    print("=" * 70)
    print("Requirement: NO mock data, NO fake data, NO placeholders")
    print("Expected: Return empty list [] when no real data available")
    print("=" * 70)
    
    # Test with various sports and event IDs
    test_cases = [
        ("basketball_nba", "401705956"),  # NBA game
        ("icehockey_nhl", "401459528"),     # NHL game
        ("soccer_epl", "123456"),           # Likely invalid ID
        ("basketball_nba", "invalid_id"),   # Invalid ID
    ]
    
    all_passed = True
    
    for sport_key, event_id in test_cases:
        print(f"\n--- Testing {sport_key} / Event ID: {event_id} ---")
        
        try:
            props = await service.get_player_props(sport_key, event_id)
            
            if props is None:
                print(f"  ✗ FAIL: Returned None instead of empty list")
                all_passed = False
                continue
                
            if not isinstance(props, list):
                print(f"  ✗ FAIL: Returned {type(props).__name__} instead of list")
                all_passed = False
                continue
            
            # Check for mock data indicators
            mock_indicators = [
                "mock", "fake", "placeholder", "default_", "Player 1", "Player 2",
                "Unknown Player", "Test Player", "Sample"
            ]
            
            has_mock_data = False
            for prop in props:
                player_name = str(prop.get("player", "")).lower()
                prop_id = str(prop.get("id", "")).lower()
                
                for indicator in mock_indicators:
                    if indicator.lower() in player_name or indicator.lower() in prop_id:
                        print(f"  ✗ FAIL: Found mock data indicator '{indicator}' in prop: {prop}")
                        has_mock_data = True
                        all_passed = False
                        break
                
                # Check for default_ prefix in IDs (mock data signature)
                if "default_" in prop_id:
                    print(f"  ✗ FAIL: Found default_ prefix (mock signature) in ID: {prop_id}")
                    has_mock_data = True
                    all_passed = False
            
            if not has_mock_data:
                if len(props) == 0:
                    print(f"  ✓ PASS: Returned empty list [] (no real data available)")
                else:
                    print(f"  ✓ PASS: Returned {len(props)} props with real ESPN data")
                    # Show first prop as sample
                    if props:
                        first_prop = props[0]
                        print(f"    Sample: {first_prop.get('player')} - {first_prop.get('prediction')}")
            
        except Exception as e:
            print(f"  ✗ FAIL: Exception occurred: {e}")
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED: Player props only use real ESPN data")
        print("✓ No mock data, fake data, or placeholders detected")
    else:
        print("✗ SOME TESTS FAILED: Issues detected with player props")
    print("=" * 70)
    
    await service.close()
    return all_passed

if __name__ == "__main__":
    result = asyncio.run(test_player_props_real_data())
    sys.exit(0 if result else 1)
