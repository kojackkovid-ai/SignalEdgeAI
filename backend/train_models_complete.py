#!/usr/bin/env python3
"""
Complete Model Training Script with Full Feature Support
Trains all ML models with proper synthetic data generation
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import os
from pathlib import Path
import json
from typing import Dict, List, Tuple, Any

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.enhanced_ml_service import EnhancedMLService
from app.services.data_preprocessing import AdvancedFeatureEngineer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('training_complete.log')
    ]
)
logger = logging.getLogger(__name__)

# Training configurations for all sports
TRAINING_CONFIGS = [
    # NBA
    ('basketball_nba', 'moneyline'),
    ('basketball_nba', 'spread'),
    ('basketball_nba', 'total'),
    # NFL
    ('americanfootball_nfl', 'moneyline'),
    ('americanfootball_nfl', 'spread'),
    ('americanfootball_nfl', 'total'),
    # MLB
    ('baseball_mlb', 'moneyline'),
    ('baseball_mlb', 'total'),
    # NHL
    ('icehockey_nhl', 'moneyline'),
    ('icehockey_nhl', 'puck_line'),
    ('icehockey_nhl', 'total'),
    # Soccer leagues
    ('soccer_epl', 'moneyline'),
    ('soccer_epl', 'spread'),
    ('soccer_epl', 'total'),
    ('soccer_usa_mls', 'moneyline'),
    ('soccer_usa_mls', 'spread'),
    ('soccer_usa_mls', 'total'),
    ('soccer_esp.1', 'moneyline'),
    ('soccer_esp.1', 'spread'),
    ('soccer_esp.1', 'total'),
    ('soccer_ita.1', 'moneyline'),
    ('soccer_ita.1', 'spread'),
    ('soccer_ita.1', 'total'),
    ('soccer_ger.1', 'moneyline'),
    ('soccer_ger.1', 'spread'),
    ('soccer_ger.1', 'total'),
    ('soccer_fra.1', 'moneyline'),
    ('soccer_fra.1', 'spread'),
    ('soccer_fra.1', 'total'),
]

def generate_complete_synthetic_data(sport_key: str, market_type: str, n_samples: int = 500) -> pd.DataFrame:
    """
    Generate complete synthetic training data with ALL required features
    """
    np.random.seed(42)
    data = {}
    
    # Basic record features
    data['home_wins'] = np.random.randint(10, 50, n_samples)
    data['home_losses'] = np.random.randint(5, 30, n_samples)
    data['away_wins'] = np.random.randint(10, 50, n_samples)
    data['away_losses'] = np.random.randint(5, 30, n_samples)
    
    # Recent form
    data['home_recent_wins'] = np.random.randint(0, 6, n_samples)
    data['away_recent_wins'] = np.random.randint(0, 6, n_samples)
    data['home_previous_wins'] = np.random.randint(0, 6, n_samples)
    data['away_previous_wins'] = np.random.randint(0, 6, n_samples)
    
    # Home/Away splits
    data['home_home_wins'] = np.random.randint(5, 25, n_samples)
    data['home_home_losses'] = np.random.randint(2, 15, n_samples)
    data['home_away_wins'] = np.random.randint(5, 25, n_samples)
    data['home_away_losses'] = np.random.randint(2, 15, n_samples)
    data['away_home_wins'] = np.random.randint(5, 25, n_samples)
    data['away_home_losses'] = np.random.randint(2, 15, n_samples)
    data['away_away_wins'] = np.random.randint(5, 25, n_samples)
    data['away_away_losses'] = np.random.randint(2, 15, n_samples)
    
    # Points/Goals
    if 'soccer' in sport_key:
        data['home_goals_for'] = np.random.uniform(1.0, 2.5, n_samples)
        data['home_goals_against'] = np.random.uniform(0.8, 2.0, n_samples)
        data['away_goals_for'] = np.random.uniform(1.0, 2.5, n_samples)
        data['away_goals_against'] = np.random.uniform(0.8, 2.0, n_samples)
        data['home_matches_played'] = np.random.randint(10, 40, n_samples)
        data['away_matches_played'] = np.random.randint(10, 40, n_samples)
        data['home_expected_goals'] = np.random.uniform(1.2, 2.8, n_samples)
        data['away_expected_goals'] = np.random.uniform(1.2, 2.8, n_samples)
        data['home_shots'] = np.random.uniform(10, 18, n_samples)
        data['away_shots'] = np.random.uniform(10, 18, n_samples)
        data['home_possession_pct'] = np.random.uniform(45, 60, n_samples)
        data['away_possession_pct'] = np.random.uniform(45, 60, n_samples)
        data['home_pass_completion_pct'] = np.random.uniform(75, 90, n_samples)
        data['away_pass_completion_pct'] = np.random.uniform(75, 90, n_samples)
        data['home_yellow_cards'] = np.random.uniform(1, 3, n_samples)
        data['away_yellow_cards'] = np.random.uniform(1, 3, n_samples)
        data['home_clean_sheets'] = np.random.randint(0, 15, n_samples)
        data['away_clean_sheets'] = np.random.randint(0, 15, n_samples)
    elif sport_key == 'baseball_mlb':
        data['home_runs_scored'] = np.random.uniform(4.0, 5.5, n_samples)
        data['home_runs_allowed'] = np.random.uniform(4.0, 5.5, n_samples)
        data['away_runs_scored'] = np.random.uniform(4.0, 5.5, n_samples)
        data['away_runs_allowed'] = np.random.uniform(4.0, 5.5, n_samples)
        data['home_hits'] = np.random.uniform(8, 10, n_samples)
        data['away_hits'] = np.random.uniform(8, 10, n_samples)
        data['home_walks'] = np.random.uniform(3, 4, n_samples)
        data['away_walks'] = np.random.uniform(3, 4, n_samples)
        data['home_hit_by_pitch'] = np.random.uniform(0.2, 0.5, n_samples)
        data['away_hit_by_pitch'] = np.random.uniform(0.2, 0.5, n_samples)
        data['home_at_bats'] = np.random.uniform(33, 38, n_samples)
        data['away_at_bats'] = np.random.uniform(33, 38, n_samples)
        data['home_sacrifice_flies'] = np.random.uniform(0.3, 0.6, n_samples)
        data['away_sacrifice_flies'] = np.random.uniform(0.3, 0.6, n_samples)
        data['home_singles'] = np.random.uniform(5, 7, n_samples)
        data['away_singles'] = np.random.uniform(5, 7, n_samples)
        data['home_doubles'] = np.random.uniform(1.5, 2.5, n_samples)
        data['away_doubles'] = np.random.uniform(1.5, 2.5, n_samples)
        data['home_triples'] = np.random.uniform(0.1, 0.3, n_samples)
        data['away_triples'] = np.random.uniform(0.1, 0.3, n_samples)
        data['home_home_runs'] = np.random.uniform(1.0, 1.8, n_samples)
        data['away_home_runs'] = np.random.uniform(1.0, 1.8, n_samples)
        data['home_earned_runs'] = np.random.uniform(3.5, 5.0, n_samples)
        data['away_earned_runs'] = np.random.uniform(3.5, 5.0, n_samples)
        data['home_innings_pitched'] = np.random.uniform(8.5, 9.5, n_samples)
        data['away_innings_pitched'] = np.random.uniform(8.5, 9.5, n_samples)
        data['home_strikeouts'] = np.random.uniform(8, 10, n_samples)
        data['away_strikeouts'] = np.random.uniform(8, 10, n_samples)
        data['home_putouts'] = np.random.uniform(24, 27, n_samples)
        data['away_putouts'] = np.random.uniform(24, 27, n_samples)
        data['home_assists'] = np.random.uniform(8, 12, n_samples)
        data['away_assists'] = np.random.uniform(8, 12, n_samples)
        data['home_errors'] = np.random.uniform(0.3, 0.8, n_samples)
        data['away_errors'] = np.random.uniform(0.3, 0.8, n_samples)
    elif sport_key == 'icehockey_nhl':
        data['home_goals_for'] = np.random.uniform(2.8, 3.5, n_samples)
        data['home_goals_against'] = np.random.uniform(2.5, 3.2, n_samples)
        data['away_goals_for'] = np.random.uniform(2.8, 3.5, n_samples)
        data['away_goals_against'] = np.random.uniform(2.5, 3.2, n_samples)
        data['home_time_on_ice'] = np.random.uniform(3500, 3700, n_samples)
        data['away_time_on_ice'] = np.random.uniform(3500, 3700, n_samples)
        data['home_shots_on_goal'] = np.random.uniform(30, 35, n_samples)
        data['away_shots_on_goal'] = np.random.uniform(30, 35, n_samples)
        data['home_shots_against'] = np.random.uniform(28, 33, n_samples)
        data['away_shots_against'] = np.random.uniform(28, 33, n_samples)
        data['home_missed_shots'] = np.random.uniform(8, 12, n_samples)
        data['away_missed_shots'] = np.random.uniform(8, 12, n_samples)
        data['home_missed_shots_against'] = np.random.uniform(8, 12, n_samples)
        data['away_missed_shots_against'] = np.random.uniform(8, 12, n_samples)
        data['home_blocked_shots'] = np.random.uniform(12, 18, n_samples)
        data['away_blocked_shots'] = np.random.uniform(12, 18, n_samples)
        data['home_blocked_shots_against'] = np.random.uniform(12, 18, n_samples)
        data['away_blocked_shots_against'] = np.random.uniform(12, 18, n_samples)
        data['home_power_play_goals'] = np.random.uniform(0.5, 1.0, n_samples)
        data['away_power_play_goals'] = np.random.uniform(0.5, 1.0, n_samples)
        data['home_power_play_opportunities'] = np.random.uniform(2.5, 3.5, n_samples)
        data['away_power_play_opportunities'] = np.random.uniform(2.5, 3.5, n_samples)
        data['home_power_play_goals_against'] = np.random.uniform(0.4, 0.9, n_samples)
        data['away_power_play_goals_against'] = np.random.uniform(0.4, 0.9, n_samples)
        data['home_penalty_kill_opportunities'] = np.random.uniform(2.5, 3.5, n_samples)
        data['away_penalty_kill_opportunities'] = np.random.uniform(2.5, 3.5, n_samples)
    else:  # NBA, NFL, NCAAB
        data['home_points_for'] = np.random.uniform(105, 120, n_samples) if 'basketball' in sport_key else np.random.uniform(22, 28, n_samples)
        data['home_points_against'] = np.random.uniform(105, 120, n_samples) if 'basketball' in sport_key else np.random.uniform(22, 28, n_samples)
        data['away_points_for'] = np.random.uniform(105, 120, n_samples) if 'basketball' in sport_key else np.random.uniform(22, 28, n_samples)
        data['away_points_against'] = np.random.uniform(105, 120, n_samples) if 'basketball' in sport_key else np.random.uniform(22, 28, n_samples)
    
    # NFL-specific features
    if sport_key == 'americanfootball_nfl':
        data['home_total_yards'] = np.random.uniform(320, 380, n_samples)
        data['away_total_yards'] = np.random.uniform(320, 380, n_samples)
        data['home_plays'] = np.random.uniform(60, 70, n_samples)
        data['away_plays'] = np.random.uniform(60, 70, n_samples)
        data['home_drives'] = np.random.uniform(10, 14, n_samples)
        data['away_drives'] = np.random.uniform(10, 14, n_samples)
        data['home_passing_yards'] = np.random.uniform(220, 280, n_samples)
        data['away_passing_yards'] = np.random.uniform(220, 280, n_samples)
        data['home_sack_yards'] = np.random.uniform(15, 25, n_samples)
        data['away_sack_yards'] = np.random.uniform(15, 25, n_samples)
        data['home_pass_attempts'] = np.random.uniform(35, 45, n_samples)
        data['away_pass_attempts'] = np.random.uniform(35, 45, n_samples)
        data['home_sacks'] = np.random.uniform(2, 4, n_samples)
        data['away_sacks'] = np.random.uniform(2, 4, n_samples)
        data['home_interceptions'] = np.random.uniform(0.8, 1.2, n_samples)
        data['away_interceptions'] = np.random.uniform(0.8, 1.2, n_samples)
        data['home_rushing_yards'] = np.random.uniform(100, 140, n_samples)
        data['away_rushing_yards'] = np.random.uniform(100, 140, n_samples)
        data['home_rush_attempts'] = np.random.uniform(25, 32, n_samples)
        data['away_rush_attempts'] = np.random.uniform(25, 32, n_samples)
        data['home_turnovers'] = np.random.uniform(1.0, 1.5, n_samples)
        data['away_turnovers'] = np.random.uniform(1.0, 1.5, n_samples)
        data['home_third_down_conversions'] = np.random.uniform(5, 7, n_samples)
        data['away_third_down_conversions'] = np.random.uniform(5, 7, n_samples)
        data['home_third_down_attempts'] = np.random.uniform(12, 16, n_samples)
        data['away_third_down_attempts'] = np.random.uniform(12, 16, n_samples)
        data['home_red_zone_touchdowns'] = np.random.uniform(2, 3.5, n_samples)
        data['away_red_zone_touchdowns'] = np.random.uniform(2, 3.5, n_samples)
        data['home_red_zone_attempts'] = np.random.uniform(3, 5, n_samples)
        data['away_red_zone_attempts'] = np.random.uniform(3, 5, n_samples)
    
    # NBA/NCAAB-specific features
    if 'basketball' in sport_key:
        data['home_fg_made'] = np.random.uniform(38, 45, n_samples)
        data['away_fg_made'] = np.random.uniform(38, 45, n_samples)
        data['home_three_made'] = np.random.uniform(10, 15, n_samples)
        data['away_three_made'] = np.random.uniform(10, 15, n_samples)
        data['home_fg_attempted'] = np.random.uniform(82, 90, n_samples)
        data['away_fg_attempted'] = np.random.uniform(82, 90, n_samples)
        data['home_ft_attempted'] = np.random.uniform(18, 24, n_samples)
        data['away_ft_attempted'] = np.random.uniform(18, 24, n_samples)
        data['home_rebounds'] = np.random.uniform(42, 48, n_samples)
        data['away_rebounds'] = np.random.uniform(42, 48, n_samples)
        data['home_turnovers'] = np.random.uniform(12, 16, n_samples)
        data['away_turnovers'] = np.random.uniform(12, 16, n_samples)
        data['home_assists'] = np.random.uniform(22, 28, n_samples)
        data['away_assists'] = np.random.uniform(22, 28, n_samples)
        data['home_three_attempted'] = np.random.uniform(32, 40, n_samples)
        data['away_three_attempted'] = np.random.uniform(32, 40, n_samples)
        data['home_possessions_per_game'] = np.random.uniform(98, 102, n_samples)
        data['away_possessions_per_game'] = np.random.uniform(98, 102, n_samples)
    
    # Strength of schedule
    data['home_opponent_win_pct'] = np.random.uniform(0.45, 0.55, n_samples)
    data['away_opponent_win_pct'] = np.random.uniform(0.45, 0.55, n_samples)
    data['home_season_form'] = np.random.uniform(0.45, 0.65, n_samples)
    data['away_season_form'] = np.random.uniform(0.45, 0.65, n_samples)
    
    # Rest days
    data['home_rest_days'] = np.random.randint(1, 5, n_samples)
    data['away_rest_days'] = np.random.randint(1, 5, n_samples)
    # Generate dates as a list to avoid timedelta with numpy array issues
    now = datetime.now()
    data['home_last_game_date'] = [now - timedelta(days=int(d)) for d in data['home_rest_days']]
    data['away_last_game_date'] = [now - timedelta(days=int(d)) for d in data['away_rest_days']]

    
    # Travel
    data['home_travel_miles'] = np.random.uniform(0, 500, n_samples)
    data['away_travel_miles'] = np.random.uniform(100, 1500, n_samples)
    data['home_time_zones_traveled'] = np.random.randint(0, 2, n_samples)
    data['away_time_zones_traveled'] = np.random.randint(0, 3, n_samples)
    
    # Historical H2H
    data['historical_h2h_home_wins'] = np.random.randint(5, 20, n_samples)
    data['historical_h2h_away_wins'] = np.random.randint(5, 20, n_samples)
    data['recent_h2h_wins_home'] = np.random.randint(1, 4, n_samples)
    data['season_series_home_wins'] = np.random.randint(0, 3, n_samples)
    data['season_series_away_wins'] = np.random.randint(0, 3, n_samples)
    
    # vs top teams
    data['home_vs_top_teams_wins'] = np.random.randint(3, 15, n_samples)
    data['home_vs_top_teams_losses'] = np.random.randint(2, 10, n_samples)
    data['away_vs_top_teams_wins'] = np.random.randint(3, 15, n_samples)
    data['away_vs_top_teams_losses'] = np.random.randint(2, 10, n_samples)
    
    # Close games
    data['home_close_games_wins'] = np.random.randint(5, 15, n_samples)
    data['home_close_games_losses'] = np.random.randint(3, 10, n_samples)
    data['away_close_games_wins'] = np.random.randint(5, 15, n_samples)
    data['away_close_games_losses'] = np.random.randint(3, 10, n_samples)
    
    # ATS features
    data['home_ats_wins'] = np.random.randint(15, 35, n_samples)
    data['home_ats_losses'] = np.random.randint(10, 25, n_samples)
    data['away_ats_wins'] = np.random.randint(15, 35, n_samples)
    data['away_ats_losses'] = np.random.randint(10, 25, n_samples)
    data['home_avg_margin_vs_spread'] = np.random.uniform(-2, 2, n_samples)
    data['away_avg_margin_vs_spread'] = np.random.uniform(-2, 2, n_samples)
    data['home_recent_ats_wins'] = np.random.randint(2, 5, n_samples)
    data['away_recent_ats_wins'] = np.random.randint(2, 5, n_samples)
    
    # Over/Under features
    data['home_over_wins'] = np.random.randint(15, 30, n_samples)
    data['home_under_wins'] = np.random.randint(15, 30, n_samples)
    data['away_over_wins'] = np.random.randint(15, 30, n_samples)
    data['away_under_wins'] = np.random.randint(15, 30, n_samples)
    
    # Consistency
    data['home_points_mean'] = np.random.uniform(100, 115, n_samples) if 'basketball' in sport_key else np.random.uniform(2.5, 3.5, n_samples)
    data['away_points_mean'] = np.random.uniform(100, 115, n_samples) if 'basketball' in sport_key else np.random.uniform(2.5, 3.5, n_samples)
    data['home_points_std'] = np.random.uniform(8, 15, n_samples)
    data['away_points_std'] = np.random.uniform(8, 15, n_samples)
    
    # Weather (for outdoor sports)
    data['temperature'] = np.random.uniform(40, 80, n_samples)
    data['wind_speed'] = np.random.uniform(5, 15, n_samples)
    data['precipitation'] = np.random.uniform(0, 0.2, n_samples)
    data['wind_direction'] = np.random.uniform(0, 360, n_samples)
    
    # Injury features
    data['home_injured_players'] = np.random.randint(0, 5, n_samples)
    data['away_injured_players'] = np.random.randint(0, 5, n_samples)
    data['home_star_players_injured'] = np.random.randint(0, 2, n_samples)
    data['away_star_players_injured'] = np.random.randint(0, 2, n_samples)
    data['home_injury_performance_impact'] = np.random.uniform(0, 0.1, n_samples)
    data['away_injury_performance_impact'] = np.random.uniform(0, 0.1, n_samples)
    
    # Position-specific injuries
    data['home_point_guard_injured'] = np.random.choice([0, 1], n_samples, p=[0.9, 0.1])
    data['home_center_injured'] = np.random.choice([0, 1], n_samples, p=[0.9, 0.1])
    data['away_point_guard_injured'] = np.random.choice([0, 1], n_samples, p=[0.9, 0.1])
    data['away_center_injured'] = np.random.choice([0, 1], n_samples, p=[0.9, 0.1])
    data['home_quarterback_injured'] = np.random.choice([0, 1], n_samples, p=[0.95, 0.05])
    data['home_running_back_injured'] = np.random.choice([0, 1], n_samples, p=[0.9, 0.1])
    data['home_wide_receiver_injured'] = np.random.choice([0, 1], n_samples, p=[0.9, 0.1])
    data['away_quarterback_injured'] = np.random.choice([0, 1], n_samples, p=[0.95, 0.05])
    data['away_running_back_injured'] = np.random.choice([0, 1], n_samples, p=[0.9, 0.1])
    data['away_wide_receiver_injured'] = np.random.choice([0, 1], n_samples, p=[0.9, 0.1])
    data['home_ace_pitcher_injured'] = np.random.choice([0, 1], n_samples, p=[0.9, 0.1])
    data['home_closer_injured'] = np.random.choice([0, 1], n_samples, p=[0.9, 0.1])
    data['away_ace_pitcher_injured'] = np.random.choice([0, 1], n_samples, p=[0.9, 0.1])
    data['away_closer_injured'] = np.random.choice([0, 1], n_samples, p=[0.9, 0.1])
    
    # Market lines
    data['spread_line'] = np.random.uniform(-7, 7, n_samples)
    data['total_line'] = np.random.uniform(210, 230, n_samples) if 'basketball' in sport_key else np.random.uniform(42, 50, n_samples)
    
    # Game scores (for target variable)
    if 'soccer' in sport_key:
        data['home_score'] = np.random.randint(0, 4, n_samples)
        data['away_score'] = np.random.randint(0, 4, n_samples)
    elif sport_key == 'baseball_mlb':
        data['home_score'] = np.random.randint(2, 8, n_samples)
        data['away_score'] = np.random.randint(2, 8, n_samples)
    elif sport_key == 'icehockey_nhl':
        data['home_score'] = np.random.randint(1, 5, n_samples)
        data['away_score'] = np.random.randint(1, 5, n_samples)
    else:
        data['home_score'] = np.random.randint(95, 125, n_samples) if 'basketball' in sport_key else np.random.randint(14, 35, n_samples)
        data['away_score'] = np.random.randint(95, 125, n_samples) if 'basketball' in sport_key else np.random.randint(14, 35, n_samples)
    
    # Game date
    data['game_date'] = [datetime.now() - timedelta(days=np.random.randint(1, 90)) for _ in range(n_samples)]
    
    return pd.DataFrame(data)

async def train_single_model(sport_key: str, market_type: str, ml_service: EnhancedMLService) -> Dict[str, Any]:
    """Train a single model configuration"""
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"Training {sport_key} - {market_type}")
        logger.info(f"{'='*60}")
        
        # Generate synthetic training data
        logger.info("Generating synthetic training data...")
        training_data = generate_complete_synthetic_data(sport_key, market_type, n_samples=500)
        logger.info(f"Generated {len(training_data)} training samples with {len(training_data.columns)} features")
        
        # Train models
        logger.info("Training models...")
        result = await ml_service.train_models(
            sport_key=sport_key,
            market_type=market_type,
            training_data=training_data.to_dict('records')
        )

        
        if result.get('success'):
            logger.info(f"✅ Successfully trained {len(result.get('models', []))} models")
            return {
                'sport_key': sport_key,
                'market_type': market_type,
                'success': True,
                'models_trained': len(result.get('models', []))
            }
        else:
            logger.error(f"❌ Training failed: {result.get('error', 'Unknown error')}")
            return {
                'sport_key': sport_key,
                'market_type': market_type,
                'success': False,
                'error': result.get('error', 'Unknown error')
            }
            
    except Exception as e:
        logger.error(f"❌ Error training {sport_key} - {market_type}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'sport_key': sport_key,
            'market_type': market_type,
            'success': False,
            'error': str(e)
        }

async def main():
    """Main training function"""
    print("="*70)
    print("SPORTS PREDICTION MODEL TRAINING - COMPLETE VERSION")
    print("="*70)
    
    # Initialize ML service
    ml_service = EnhancedMLService()
    
    results = []
    successful = 0
    failed = 0
    
    # Train all configurations
    for sport_key, market_type in TRAINING_CONFIGS:
        result = await train_single_model(sport_key, market_type, ml_service)
        results.append(result)
        
        if result['success']:
            successful += 1
        else:
            failed += 1
    
    # Print summary
    print("\n" + "="*70)
    print("TRAINING SUMMARY")
    print("="*70)
    print(f"Total configurations: {len(TRAINING_CONFIGS)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"Success rate: {successful/max(1, len(TRAINING_CONFIGS)) * 100:.1f}%")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"training_results_complete_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total': len(TRAINING_CONFIGS),
            'successful': successful,
            'failed': failed,
            'results': results
        }, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    print("="*70)
    
    return successful, failed

if __name__ == "__main__":
    try:
        successful, failed = asyncio.run(main())
        sys.exit(0 if successful > 0 else 1)
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
