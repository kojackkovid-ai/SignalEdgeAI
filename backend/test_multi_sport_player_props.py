#!/usr/bin/env python3
"""
Test script to verify multi-sport player props with reasoning and tier functionality
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.espn_prediction_service import ESPNPredictionService
from app.services.ml_service import MLService

async def test_multi_sport_player_props():
    """Test player props for different sports with reasoning"""
    
    print("🧪 Testing Multi-Sport Player Props with Reasoning")
    print("=" * 60)
    
    # Initialize services
    espn_service = ESPNPredictionService()
    ml_service = MLService()
    
    # Test data for different sports
    test_cases = [
        {
            "sport": "NBA",
            "sport_key": "basketball_nba",
            "player": "LeBron James",
            "position": "SF",
            "team": "Lakers",
            "prop_type": "points",
            "line": 25.5,
            "season_avg": 28.2
        },
        {
            "sport": "NHL", 
            "sport_key": "icehockey_nhl",
            "player": "Connor McDavid",
            "position": "C",
            "team": "Oilers", 
            "prop_type": "goals",
            "line": 0.5,
            "season_avg": 0.8
        },
        {
            "sport": "NFL",
            "sport_key": "americanfootball_nfl", 
            "player": "Patrick Mahomes",
            "position": "QB",
            "team": "Chiefs",
            "prop_type": "passing_yards", 
            "line": 275.5,
            "season_avg": 295.0
        },
        {
            "sport": "Soccer",
            "sport_key": "soccer_epl",
            "player": "Harry Kane", 
            "position": "ST",
            "team": "Tottenham",
            "prop_type": "goals",
            "line": 0.5,
            "season_avg": 0.9
        }
    ]
    
    all_props = []
    
    for test_case in test_cases:
        print(f"\n🏀⚽🏈 Testing {test_case['sport']} - {test_case['player']}")
        print("-" * 40)
        
        try:
            # Test ML service directly
            prediction = await ml_service.predict_player_prop_espn(
                player_name=test_case["player"],
                prop_type=test_case["prop_type"], 
                line=test_case["line"],
                season_avg=test_case["season_avg"],
                position=test_case["position"],
                team_name=test_case["team"],
                sport_key=test_case["sport_key"]
            )
            
            if prediction:
                print(f"✅ Prediction generated successfully")
                print(f"   Confidence: {prediction.get('confidence', 'N/A')}")
                print(f"   Prediction: {prediction.get('prediction', 'N/A')}")
                
                if "reasoning" in prediction and prediction["reasoning"]:
                    print(f"   Reasoning points: {len(prediction['reasoning'])}")
                    for i, reason in enumerate(prediction["reasoning"], 1):
                        print(f"   {i}. {reason['factor']}: {reason['explanation']}")
                else:
                    print("   ⚠️  No reasoning generated")
                    
                if "models" in prediction:
                    print(f"   Models: {len(prediction['models'])} ensemble models")
                    
                # Create a mock prop structure like the ESPN service would
                mock_prop = {
                    "id": f"test_{test_case['sport_key']}_{test_case['prop_type']}_{test_case['player']}",
                    "market_key": f"player_{test_case['prop_type']}",
                    "player": test_case["player"],
                    "point": test_case["line"],
                    "sport_key": test_case["sport_key"],
                    "sport": test_case["sport"],
                    "prediction_type": "player_prop",
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "odds": "-110",
                    **prediction
                }
                
                all_props.append(mock_prop)
                
            else:
                print(f"❌ No prediction generated")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n📊 Summary")
    print("=" * 60)
    print(f"Total props generated: {len(all_props)}")
    
    # Group by sport
    by_sport = {}
    for prop in all_props:
        sport = prop["sport"]
        if sport not in by_sport:
            by_sport[sport] = []
        by_sport[sport].append(prop)
    
    for sport, props in by_sport.items():
        print(f"{sport}: {len(props)} props")
        
    # Test tier filtering simulation
    print(f"\n🔒 Tier Functionality Test")
    print("=" * 60)
    
    tier_configs = {
        "Free": {"reasoning": False, "models": False},
        "Starter": {"reasoning": False, "models": False}, 
        "Basic": {"reasoning": True, "models": False},
        "Pro": {"reasoning": True, "models": True},
        "Elite": {"reasoning": True, "models": True}
    }
    
    for tier, config in tier_configs.items():
        print(f"\n👤 {tier} Tier:")
        
        # Simulate what a user would see
        for prop in all_props[:2]:  # Show first 2 props
            filtered_prop = {}
            
            # Always include basic fields
            for field in ["id", "market_key", "player", "point", "sport", "prediction", "confidence"]:
                if field in prop:
                    filtered_prop[field] = prop[field]
            
            # Include reasoning if tier allows
            if config["reasoning"] and "reasoning" in prop:
                filtered_prop["reasoning"] = prop["reasoning"]
                
            # Include models if tier allows  
            if config["models"] and "models" in prop:
                filtered_prop["models"] = prop["models"]
            
            print(f"   {prop['player']} ({prop['sport']}): {len(filtered_prop)} fields visible")
            if "reasoning" in filtered_prop:
                print(f"     └─ Reasoning: {len(filtered_prop['reasoning'])} points")
            if "models" in filtered_prop:
                print(f"     └─ Models: {len(filtered_prop['models'])} models")
    
    print(f"\n✅ Multi-sport player props test completed!")
    return all_props

if __name__ == "__main__":
    asyncio.run(test_multi_sport_player_props())