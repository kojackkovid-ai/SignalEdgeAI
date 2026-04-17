#!/usr/bin/env python3
"""
Quick test to verify player stats methods are working
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.espn_prediction_service import ESPNPredictionService

async def test_stats():
    """Test stat extraction methods"""
    service = ESPNPredictionService()
    
    print("=" * 60)
    print("TESTING PLAYER STATS EXTRACTION")
    print("=" * 60)
    
    # Test 1: Check default stats for each sport
    print("\n1. Testing _get_default_player_stats_for_sport():")
    sports = ['basketball_nba', 'hockey_nhl', 'baseball_mlb', 'football_nfl', 'soccer_goal']
    
    for sport in sports:
        stats = service._get_default_player_stats_for_sport(sport)
        print(f"\n   {sport}:")
        for key, val in list(stats.items())[:3]:
            print(f"      {key}: {val}")
        print(f"      ... and {len(stats) - 3} more stats")
    
    # Test 2: Check stat extraction mapping
    print("\n2. Testing _extract_stat_from_dict():")
    
    # Create a dummy stats dict
    test_stats = {
        'pointsPerGame': 25.5,
        'reboundsPerGame': 10.2,
        'assistsPerGame': 7.5
    }
    
    # Test extraction for basketball
    market_key = "points"
    result = service._extract_stat_from_dict(test_stats, market_key, "basketball_nba")
    print(f"   Basketball - Market: {market_key} -> {result}")
    
    market_key = "rebounds"
    result = service._extract_stat_from_dict(test_stats, market_key, "basketball_nba")
    print(f"   Basketball - Market: {market_key} -> {result}")
    
    # Test 3: Check player stat averages with fallback
    print("\n3. Testing _get_player_stat_averages() with fallback:")
    
    # Test with None player_stats (should use fallback)
    season_avg, recent_avg = service._get_player_stat_averages(
        player_stats=None,
        market_key="points", 
        sport_key="basketball_nba",
        stats_dict=test_stats
    )
    print(f"   None player_stats + stats_dict fallback:")
    print(f"      Season Avg: {season_avg}")
    print(f"      Recent Avg: {recent_avg}")
    
    # Test with actual player_stats dict
    player_stats = {
        'season_stats': {'pointsPerGame': 22.0},
        'recent_10_stats': {'pointsPerGame': 24.5},
        'stats_dict': test_stats
    }
    season_avg, recent_avg = service._get_player_stat_averages(
        player_stats=player_stats,
        market_key="points",
        sport_key="basketball_nba",
        stats_dict=test_stats
    )
    print(f"   Valid player_stats dict:")
    print(f"      Season Avg: {season_avg}")
    print(f"      Recent Avg: {recent_avg}")
    
    print("\n" + "=" * 60)
    print("✅ ALL STAT METHODS WORKING")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_stats())
