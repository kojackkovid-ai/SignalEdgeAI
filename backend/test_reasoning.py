#!/usr/bin/env python3
"""
Test script to verify unique reasoning generation for predictions.
"""
import asyncio
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent))

from app.services.enhanced_ml_service import EnhancedMLService

async def test_reasoning_generation():
    """Test that reasoning is unique for different games"""
    print("="*70)
    print("Testing Unique Reasoning Generation")
    print("="*70)
    
    service = EnhancedMLService()
    
    # Test game data for different matchups
    test_games = [
        {
            "event_id": "game_001",
            "home_team": "Duke",
            "away_team": "North Carolina",
            "home_wins": 15,
            "home_losses": 3,
            "away_wins": 12,
            "away_losses": 6,
            "home_recent_wins": 4,
            "away_recent_wins": 3,
            "home_points_per_game": 78.5,
            "away_points_per_game": 72.3,
            "venue": "Cameron Indoor Stadium",
            "odds_data": {"home_odds": -150, "away_odds": +130}
        },
        {
            "event_id": "game_002",
            "home_team": "Kentucky",
            "away_team": "Florida",
            "home_wins": 18,
            "home_losses": 2,
            "away_wins": 10,
            "away_losses": 8,
            "home_recent_wins": 5,
            "away_recent_wins": 2,
            "home_points_per_game": 82.1,
            "away_points_per_game": 68.5,
            "venue": "Rupp Arena",
            "odds_data": {"home_odds": -200, "away_odds": +170}
        },
        {
            "event_id": "game_003",
            "home_team": "Kansas",
            "away_team": "Baylor",
            "home_wins": 14,
            "home_losses": 4,
            "away_wins": 16,
            "away_losses": 2,
            "home_recent_wins": 3,
            "away_recent_wins": 4,
            "home_points_per_game": 75.2,
            "away_points_per_game": 79.8,
            "venue": "Allen Fieldhouse",
            "odds_data": {"home_odds": -110, "away_odds": -110}
        }
    ]
    
    all_reasonings = []
    
    for i, game in enumerate(test_games, 1):
        print(f"\n{i}. Testing {game['home_team']} vs {game['away_team']}...")
        
        # Generate reasoning using the service
        reasoning = service._generate_unique_reasoning(
            game_data=game,
            prediction=f"{game['home_team']} Win",
            confidence=72.5,
            individual_predictions={
                'xgboost': [0.3, 0.7],
                'lightgbm': [0.25, 0.75],
                'random_forest': [0.35, 0.65]
            },
            sport_key='basketball_ncaa',
            market_type='moneyline'
        )
        
        all_reasonings.append(reasoning)
        
        print(f"   Generated {len(reasoning)} reasoning points:")
        for j, r in enumerate(reasoning[:4], 1):  # Show top 4
            print(f"   {j}. {r['factor']} (Impact: {r['impact']}, Weight: {r['weight']})")
            print(f"      {r['explanation'][:80]}...")
    
    # Verify uniqueness
    print("\n" + "="*70)
    print("Verifying Uniqueness")
    print("="*70)
    
    # Compare first reasoning points of each game
    first_factors = [r[0]['explanation'] for r in all_reasonings]
    unique_count = len(set(first_factors))
    
    print(f"\nFirst reasoning factors are {'UNIQUE' if unique_count == len(test_games) else 'DUPLICATED'}")
    print(f"Unique explanations: {unique_count}/{len(test_games)}")
    
    # Check for duplicate explanations
    all_explanations = []
    for reasoning in all_reasonings:
        all_explanations.extend([r['explanation'] for r in reasoning])
    
    duplicates = len(all_explanations) - len(set(all_explanations))
    print(f"Total duplicate explanations across all games: {duplicates}")
    
    if duplicates == 0:
        print("\n✅ SUCCESS: All reasoning is unique!")
    else:
        print(f"\n⚠️  WARNING: {duplicates} duplicate explanations found")
    
    print("\n" + "="*70)
    print("Test Complete")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_reasoning_generation())
