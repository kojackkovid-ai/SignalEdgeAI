#!/usr/bin/env python3
"""
Comprehensive test for DataFrame fragmentation fixes
Tests all sports and market types to verify no PerformanceWarning messages appear
"""

import warnings
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Capture all warnings
warnings.filterwarnings('error', category=pd.errors.PerformanceWarning)

# Add app to path
sys.path.insert(0, 'app')

from app.services.data_preprocessing import AdvancedFeatureEngineer

def create_mock_game_data(sport_key):
    """Create realistic mock game data for testing - all values as lists"""
    now = datetime.now()
    
    base_data = {
        'home_team': ['Team A'],
        'away_team': ['Team B'],
        'game_date': [now],
        'commence_time': [now],
        
        # Basic record features
        'home_wins': [10],
        'home_losses': [5],
        'away_wins': [8],
        'away_losses': [7],
        'home_recent_wins': [4],
        'away_recent_wins': [3],
        'home_previous_wins': [3],
        'away_previous_wins': [2],
        
        # Home/away splits
        'home_home_wins': [6],
        'home_home_losses': [2],
        'home_away_wins': [4],
        'home_away_losses': [3],
        'away_home_wins': [3],
        'away_home_losses': [4],
        'away_away_wins': [5],
        'away_away_losses': [3],
        
        # Points/Goals
        'home_points_for': [110],
        'home_points_against': [105],
        'away_points_for': [108],
        'away_points_against': [110],
        'home_points_mean': [110],
        'away_points_mean': [108],
        'home_points_std': [12],
        'away_points_std': [11],
        
        # Historical features
        'historical_h2h_home_wins': [15],
        'historical_h2h_away_wins': [10],
        'recent_h2h_wins_home': [3],
        'season_series_home_wins': [2],
        'season_series_away_wins': [1],
        
        # vs top teams
        'home_vs_top_teams_wins': [5],
        'home_vs_top_teams_losses': [3],
        'away_vs_top_teams_wins': [4],
        'away_vs_top_teams_losses': [4],
        
        # Close games
        'home_close_games_wins': [6],
        'home_close_games_losses': [2],
        'away_close_games_wins': [5],
        'away_close_games_losses': [3],
        
        # ATS features
        'home_ats_wins': [8],
        'home_ats_losses': [7],
        'away_ats_wins': [7],
        'away_ats_losses': [8],
        'home_avg_margin_vs_spread': [2.5],
        'away_avg_margin_vs_spread': [-1.2],
        'home_recent_ats_wins': [3],
        'away_recent_ats_wins': [2],
        
        # OU features
        'home_over_wins': [9],
        'home_under_wins': [6],
        'away_over_wins': [8],
        'away_under_wins': [7],
        
        # Rest and schedule
        'home_rest_days': [2],
        'away_rest_days': [3],
        'home_time_zones_traveled': [0],
        'away_time_zones_traveled': [1],
        'home_last_game_date': [now - timedelta(days=2)],
        'away_last_game_date': [now - timedelta(days=3)],
        
        # Opponent strength
        'home_opponent_win_pct': [0.55],
        'away_opponent_win_pct': [0.52],
        'home_season_form': [0.65],
        'away_season_form': [0.55],
        
        # Travel
        'home_travel_miles': [0],
        'away_travel_miles': [500],
        
        # Injuries
        'home_injured_players': [2],
        'away_injured_players': [1],
        'home_star_players_injured': [0],
        'away_star_players_injured': [1],
        'home_injury_performance_impact': [0.02],
        'away_injury_performance_impact': [0.05],
        
        # Weather
        'temperature': [72],
        'wind_speed': [5],
        'precipitation': [0],
        'wind_direction': [0],
        
        # Market lines
        'spread_line': [-3.5],
        'total_line': [220.5],
        'home_score': [112],
        'away_score': [108],
    }
    
    # Sport-specific features - ALL AS LISTS
    if sport_key in ['basketball_nba', 'basketball_ncaa']:
        base_data.update({
            'home_possessions_per_game': [100],
            'away_possessions_per_game': [98],
            'home_fg_made': [40],
            'home_fg_attempted': [85],
            'away_fg_made': [38],
            'away_fg_attempted': [82],
            'home_three_made': [12],
            'home_three_attempted': [35],
            'away_three_made': [10],
            'away_three_attempted': [32],
            'home_ft_attempted': [20],
            'away_ft_attempted': [18],
            'home_rebounds': [44],
            'away_rebounds': [42],
            'home_turnovers': [14],
            'away_turnovers': [13],
            'home_assists': [25],
            'away_assists': [22],
            'home_point_guard_injured': [False],
            'home_center_injured': [False],
            'away_point_guard_injured': [False],
            'away_center_injured': [True],
        })
    
    elif sport_key == 'americanfootball_nfl':
        base_data.update({
            'home_total_yards': [350],
            'away_total_yards': [320],
            'home_plays': [60],
            'away_plays': [58],
            'home_drives': [12],
            'away_drives': [11],
            'home_passing_yards': [250],
            'away_passing_yards': [220],
            'home_sack_yards': [15],
            'away_sack_yards': [20],
            'home_pass_attempts': [35],
            'away_pass_attempts': [32],
            'home_sacks': [2],
            'away_sacks': [3],
            'home_interceptions': [1],
            'away_interceptions': [2],
            'home_rushing_yards': [100],
            'away_rushing_yards': [100],
            'home_rush_attempts': [25],
            'away_rush_attempts': [26],
            'home_turnovers': [1],
            'away_turnovers': [2],
            'home_third_down_conversions': [6],
            'home_third_down_attempts': [12],
            'away_third_down_conversions': [5],
            'away_third_down_attempts': [11],
            'home_red_zone_touchdowns': [3],
            'home_red_zone_attempts': [4],
            'away_red_zone_touchdowns': [2],
            'away_red_zone_attempts': [4],
            'home_quarterback_injured': [False],
            'home_running_back_injured': [False],
            'home_wide_receiver_injured': [False],
            'away_quarterback_injured': [False],
            'away_running_back_injured': [False],
            'away_wide_receiver_injured': [True],
        })
    
    elif sport_key == 'baseball_mlb':
        base_data.update({
            'home_runs_scored': [5],
            'home_runs_allowed': [3],
            'away_runs_scored': [4],
            'away_runs_allowed': [4],
            'home_hits': [10],
            'away_hits': [8],
            'home_walks': [3],
            'away_walks': [4],
            'home_hit_by_pitch': [1],
            'away_hit_by_pitch': [0],
            'home_at_bats': [35],
            'away_at_bats': [33],
            'home_sacrifice_flies': [1],
            'away_sacrifice_flies': [0],
            'home_singles': [6],
            'away_singles': [5],
            'home_doubles': [2],
            'away_doubles': [2],
            'home_triples': [0],
            'away_triples': [0],
            'home_home_runs': [2],
            'away_home_runs': [1],
            'home_earned_runs': [3],
            'away_earned_runs': [4],
            'home_innings_pitched': [9],
            'away_innings_pitched': [8],
            'home_strikeouts': [8],
            'away_strikeouts': [7],
            'home_putouts': [27],
            'away_putouts': [24],
            'home_assists': [12],
            'away_assists': [10],
            'home_errors': [0],
            'away_errors': [1],
            'home_ace_pitcher_injured': [False],
            'home_closer_injured': [False],
            'away_ace_pitcher_injured': [False],
            'away_closer_injured': [False],
        })
    
    elif sport_key == 'icehockey_nhl':
        base_data.update({
            'home_time_on_ice': [3600],
            'away_time_on_ice': [3600],
            'home_goals_for': [3],
            'away_goals_for': [2],
            'home_goals_against': [2],
            'away_goals_against': [3],
            'home_expected_goals_for': [2.8],
            'away_expected_goals_for': [2.5],
            'home_shots_on_goal': [30],
            'away_shots_on_goal': [28],
            'home_shots_against': [25],
            'away_shots_against': [30],
            'home_missed_shots': [12],
            'away_missed_shots': [10],
            'home_missed_shots_against': [10],
            'away_missed_shots_against': [12],
            'home_blocked_shots': [15],
            'away_blocked_shots': [14],
            'home_blocked_shots_against': [14],
            'away_blocked_shots_against': [15],
            'home_power_play_goals': [1],
            'away_power_play_goals': [0],
            'home_power_play_opportunities': [3],
            'away_power_play_opportunities': [2],
            'home_power_play_goals_against': [0],
            'away_power_play_goals_against': [1],
            'home_penalty_kill_opportunities': [2],
            'away_penalty_kill_opportunities': [3],
        })
    
    elif sport_key == 'soccer_epl':
        base_data.update({
            'home_goals_for': [45],
            'home_goals_against': [20],
            'away_goals_for': [35],
            'away_goals_against': [30],
            'home_matches_played': [19],
            'away_matches_played': [19],
            'home_expected_goals': [48],
            'away_expected_goals': [38],
            'home_shots': [180],
            'away_shots': [160],
            'home_possession_pct': [58],
            'away_possession_pct': [52],
            'home_pass_completion_pct': [85],
            'away_pass_completion_pct': [80],
            'home_yellow_cards': [25],
            'away_yellow_cards': [30],
            'home_clean_sheets': [8],
            'away_clean_sheets': [6],
        })
    
    return base_data

def test_sport_market_combination(sport_key, market_type, engineer):
    """Test a specific sport and market combination"""
    print(f"\n  Testing {sport_key} - {market_type}...")
    
    try:
        # Create mock data
        game_data = create_mock_game_data(sport_key)
        df = pd.DataFrame(game_data)
        
        # Prepare features - this should NOT raise PerformanceWarning
        X, y = engineer.prepare_features(df, sport_key, market_type)
        
        # Verify output
        assert isinstance(X, pd.DataFrame), f"Expected DataFrame, got {type(X)}"
        assert X.shape[0] == 1, f"Expected 1 row, got {X.shape[0]}"
        assert X.shape[1] > 0, f"Expected features, got {X.shape[1]}"
        assert isinstance(y, np.ndarray), f"Expected numpy array, got {type(y)}"
        assert len(y) == 1, f"Expected 1 target value, got {len(y)}"
        
        print(f"    ✅ SUCCESS: {X.shape[1]} features created, no fragmentation warnings")
        return True
        
    except pd.errors.PerformanceWarning as e:
        print(f"    ❌ FAILED: PerformanceWarning - {e}")
        return False
    except Exception as e:
        print(f"    ❌ FAILED: {type(e).__name__} - {e}")
        return False

def main():
    """Run comprehensive fragmentation fix tests"""
    print("=" * 70)
    print("DATAFRAME FRAGMENTATION FIX - COMPREHENSIVE TEST")
    print("=" * 70)
    print("\nTesting all sports and market combinations...")
    print("Any PerformanceWarning will cause the test to FAIL")
    print("-" * 70)
    
    # Initialize feature engineer
    engineer = AdvancedFeatureEngineer()
    
    # Define all sports and markets to test
    sports = [
        'basketball_nba',
        'basketball_ncaa',
        'americanfootball_nfl',
        'baseball_mlb',
        'icehockey_nhl',
        'soccer_epl'
    ]
    
    markets = ['spread', 'total', 'moneyline']
    
    # Track results
    results = []
    total_tests = 0
    passed_tests = 0
    
    # Test each combination
    for sport in sports:
        print(f"\n{sport.upper()}:")
        for market in markets:
            total_tests += 1
            if test_sport_market_combination(sport, market, engineer):
                passed_tests += 1
                results.append((sport, market, "PASS"))
            else:
                results.append((sport, market, "FAIL"))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for sport, market, status in results:
        emoji = "✅" if status == "PASS" else "❌"
        print(f"{emoji} {sport} - {market}: {status}")
    
    print("-" * 70)
    print(f"Total: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED - No DataFrame fragmentation warnings!")
        print("The pd.concat() batch column addition fix is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed")
        print("Some fragmentation warnings may still be present.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
