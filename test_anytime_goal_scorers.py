#!/usr/bin/env python3
"""Test the new anytime goal scorers roster-based method"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app.services.espn_prediction_service import ESPNPredictionService

async def test_anytime_goal_scorers():
    """Test the anytime goal scorers method"""
    service = ESPNPredictionService()

    # Test with NHL game
    sport_key = "icehockey_nhl"
    event_id = "401671790"  # Recent NHL game

    print(f"Testing anytime goal scorers for {sport_key}/{event_id}")

    try:
        result = await service.get_anytime_goal_scorers(sport_key, event_id, "NHL")
        print("SUCCESS!")
        print(f"Home team: {result.get('home_team', {}).get('name', 'N/A')}")
        home_scorers = result.get('home_team', {}).get('top_scorers', [])
        print(f"Home scorers: {len(home_scorers)}")
        for i, scorer in enumerate(home_scorers[:2]):
            print(f"  {i+1}. {scorer.get('player', 'Unknown')} (confidence: {scorer.get('confidence', 0)}%)")

        print(f"Away team: {result.get('away_team', {}).get('name', 'N/A')}")
        away_scorers = result.get('away_team', {}).get('top_scorers', [])
        print(f"Away scorers: {len(away_scorers)}")
        for i, scorer in enumerate(away_scorers[:2]):
            print(f"  {i+1}. {scorer.get('player', 'Unknown')} (confidence: {scorer.get('confidence', 0)}%)")

        print(f"Source: {result.get('source', 'unknown')}")
        if 'error' in result:
            print(f"Error: {result['error']}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

async def test_player_props():
    """Test what player props are available"""
    service = ESPNPredictionService()

    sport_key = "icehockey_nhl"
    event_id = "401671790"

    print(f"\nTesting player props for {sport_key}/{event_id}")

    try:
        props = await service.get_player_props(sport_key, event_id)
        print(f"Total props: {len(props) if props else 0}")
        
        if props:
            market_keys = set()
            for prop in props[:10]:  # Show first 10
                market_key = prop.get('market_key', 'unknown')
                market_keys.add(market_key)
                print(f"  - {market_key}: {prop.get('player_name', 'unknown')} - {prop.get('line', 'unknown')}")
            
            print(f"Market keys found: {market_keys}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_player_props())
    asyncio.run(test_anytime_goal_scorers())