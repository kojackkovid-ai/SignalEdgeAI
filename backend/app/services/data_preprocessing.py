import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
import re

logger = logging.getLogger(__name__)

class AdvancedFeatureEngineer:
    """
    Advanced feature engineering for sports prediction with domain-specific metrics
    """
    
    def __init__(self):
        self.scalers = {}
        self.encoders = {}
        self.feature_importance = {}
        
        # Sport-specific feature configurations
        self.sport_configs = {
            'basketball_nba': {
                'pace_stats': ['possessions_per_game', 'pace_factor'],
                'efficiency_stats': ['offensive_rating', 'defensive_rating', 'net_rating'],
                'shooting_stats': ['effective_fg_pct', 'true_shooting_pct', 'three_point_rate'],
                'advanced_stats': ['assist_ratio', 'turnover_ratio', 'rebound_rate']
            },
            'basketball_ncaa': {
                'pace_stats': ['possessions_per_game', 'pace_factor'],
                'efficiency_stats': ['offensive_rating', 'defensive_rating', 'net_rating'],
                'shooting_stats': ['effective_fg_pct', 'true_shooting_pct', 'three_point_rate'],
                'advanced_stats': ['assist_ratio', 'turnover_ratio', 'rebound_rate']
            },
            'americanfootball_nfl': {
                'offensive_stats': ['yards_per_play', 'points_per_drive', 'red_zone_efficiency'],
                'defensive_stats': ['yards_allowed_per_play', 'points_allowed_per_drive', 'sack_rate'],
                'passing_stats': ['net_yards_per_attempt', 'interception_rate', 'quarterback_rating'],
                'rushing_stats': ['yards_per_carry', 'success_rate', 'explosive_play_rate']
            },
            'baseball_mlb': {
                'batting_stats': ['on_base_percentage', 'slugging_percentage', 'ops', 'babip'],
                'pitching_stats': ['era_minus', 'fip', 'strikeout_rate', 'walk_rate'],
                'fielding_stats': ['defensive_efficiency', 'range_factor', 'ultimate_zone_rating'],
                'advanced_stats': ['war', 'woba', 'wrc_plus']
            },
            'icehockey_nhl': {
                'offensive_stats': ['goals_per_60', 'expected_goals_for', 'shooting_percentage'],
                'defensive_stats': ['goals_against_per_60', 'expected_goals_against', 'save_percentage'],
                'possession_stats': ['corsi_for_pct', 'fenwick_for_pct', 'zone_start_pct'],
                'special_teams': ['power_play_pct', 'penalty_kill_pct']
            },
            'soccer_epl': {
                'attacking_stats': ['goals_per_match', 'expected_goals', 'shots_per_match'],
                'defensive_stats': ['goals_against_per_match', 'expected_goals_against', 'clean_sheet_pct'],
                'possession_stats': ['possession_pct', 'pass_completion_pct', 'progressive_passes'],
                'advanced_stats': ['ppda', 'oppda', 'field_tilt']
            }
        }

    def prepare_features(self, df: pd.DataFrame, sport_key: str, market_type: str) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Prepare comprehensive features for model training
        """
        try:
            logger.info(f"Preparing features for {sport_key} - {market_type}")
            
            # Create copy to avoid modifying original data
            data = df.copy()
            
            # Basic feature engineering
            data = self._create_basic_features(data, sport_key)
            
            # Sport-specific advanced features
            data = self._create_sport_specific_features(data, sport_key)
            
            # Contextual features
            data = self._create_contextual_features(data, sport_key)
            
            # Historical features
            data = self._create_historical_features(data, sport_key)
            
            # Market-specific features
            data = self._create_market_specific_features(data, sport_key, market_type)
            
            # Weather features (if available)
            data = self._create_weather_features(data, sport_key)
            
            # Injury impact features
            data = self._create_injury_features(data, sport_key)
            
            # Target variable
            y = self._create_target_variable(data, market_type)
            
            # Feature selection and scaling
            X = self._select_and_scale_features(data, sport_key, market_type)
            
            logger.info(f"Created {X.shape[1]} features for {sport_key} - {market_type}")
            
            return X, y
            
        except Exception as e:
            logger.error(f"Error preparing features for {sport_key}: {e}")
            raise

    def prepare_single_game_features(self, game_data: Dict, sport_key: str, market_type: str) -> pd.DataFrame:
        """
        Prepare features for a single game prediction - OPTIMIZED VERSION
        Skips heavy historical feature processing for faster inference
        """
        try:
            # Convert single game data to DataFrame format
            df = pd.DataFrame([game_data])
            
            # Add placeholder columns for features that would come from historical data
            df = self._add_placeholder_features(df, sport_key)
            
            # OPTIMIZED: Use lightweight feature preparation for single games
            # This skips the heavy historical processing that blocks the event loop
            X = self._prepare_single_game_features_fast(df, sport_key, market_type)
            
            # Ensure 2D output
            if isinstance(X, pd.DataFrame):
                return X
            else:
                return pd.DataFrame(X)
            
        except Exception as e:
            logger.error(f"Error preparing single game features: {e}")
            raise

    def _prepare_single_game_features_fast(self, data: pd.DataFrame, sport_key: str, market_type: str) -> pd.DataFrame:
        """
        Fast feature preparation for single game predictions.
        Skips heavy historical aggregations and focuses on available game data.
        """
        # Start with basic features only - much faster than full pipeline
        data = self._create_basic_features(data, sport_key)
        
        # Add sport-specific features (these are computed from available stats)
        data = self._create_sport_specific_features(data, sport_key)
        
        # Add minimal contextual features (skip heavy historical lookups)
        data = self._create_minimal_contextual_features(data, sport_key)
        
        # Add market-specific features
        data = self._create_market_specific_features(data, sport_key, market_type)
        
        # Select and scale features (simplified for single game)
        X = self._select_features_fast(data, sport_key, market_type)
        
        return X

    def _create_minimal_contextual_features(self, data: pd.DataFrame, sport_key: str) -> pd.DataFrame:
        """
        Create only essential contextual features for single game prediction.
        Skips heavy historical aggregations that require database lookups.
        """
        # Build dictionary of minimal contextual features
        contextual_features = {}
        n_rows = len(data.index)
        
        # Home/away performance splits - use helper method
        home_home_wins = self._ensure_series(data, 'home_home_wins', 0)
        home_home_losses = self._ensure_series(data, 'home_home_losses', 0)
        home_away_wins = self._ensure_series(data, 'home_away_wins', 0)
        home_away_losses = self._ensure_series(data, 'home_away_losses', 0)
        
        home_home_win_pct = home_home_wins / (home_home_wins + home_home_losses + 1e-6)
        home_away_win_pct = home_away_wins / (home_away_wins + home_away_losses + 1e-6)
        contextual_features['home_home_win_pct'] = home_home_win_pct
        contextual_features['home_away_win_pct'] = home_away_win_pct
        contextual_features['home_away_diff'] = home_home_win_pct - home_away_win_pct
        
        away_home_wins = self._ensure_series(data, 'away_home_wins', 0)
        away_home_losses = self._ensure_series(data, 'away_home_losses', 0)
        away_away_wins = self._ensure_series(data, 'away_away_wins', 0)
        away_away_losses = self._ensure_series(data, 'away_away_losses', 0)
        
        away_home_win_pct = away_home_wins / (away_home_wins + away_home_losses + 1e-6)
        away_away_win_pct = away_away_wins / (away_away_wins + away_away_losses + 1e-6)
        contextual_features['away_home_win_pct'] = away_home_win_pct
        contextual_features['away_away_win_pct'] = away_away_win_pct
        contextual_features['away_away_diff'] = away_away_win_pct - away_home_win_pct
        
        # Rest days - simplified calculation
        contextual_features['home_rest_days'] = self._ensure_series(data, 'home_rest_days', 2)
        contextual_features['away_rest_days'] = self._ensure_series(data, 'away_rest_days', 2)
        contextual_features['rest_days_diff'] = contextual_features['home_rest_days'] - contextual_features['away_rest_days']
        
        # Back-to-back games
        contextual_features['home_back_to_back'] = (contextual_features['home_rest_days'] == 1).astype(int)
        contextual_features['away_back_to_back'] = (contextual_features['away_rest_days'] == 1).astype(int)
        contextual_features['back_to_back_diff'] = contextual_features['home_back_to_back'] - contextual_features['away_back_to_back']
        
        # Add all contextual features at once
        if contextual_features:
            new_cols_df = pd.DataFrame(contextual_features, index=data.index)
            data = pd.concat([data, new_cols_df], axis=1)
        
        return data

    def _select_features_fast(self, data: pd.DataFrame, sport_key: str, market_type: str) -> pd.DataFrame:
        """
        Fast feature selection for single game predictions.
        STRICTLY returns only the 7 core features that ML models were trained with.
        """
        # Get the important features list - MUST be exactly 7 features
        important_features = self._get_important_features(sport_key, market_type)
        
        # STRICT: Only use the 7 core features, no fallback to all numeric columns
        # This ensures feature count matches what models expect
        selected_features = []
        for col in important_features:
            if col in data.columns:
                selected_features.append(col)
            else:
                # Add missing features with default values (0.5 for percentages, 0 for others)
                if 'pct' in col or 'form' in col or 'sos' in col:
                    data[col] = 0.5
                else:
                    data[col] = 0
                selected_features.append(col)
        
        X = data[selected_features].copy()
        
        # Handle missing values - fill with 0.5 for percentages/form, 0 for others
        X = X.fillna(0.5)
        
        # Remove infinite values
        X = X.replace([np.inf, -np.inf], 0.5)
        
        # Final check: ensure exactly 7 features
        if X.shape[1] != 7:
            logger.warning(f"Feature count mismatch: {X.shape[1]} features, expected 7. Padding/truncating.")
            # Force exactly 7 columns by reindexing
            while X.shape[1] < 7:
                X[f'extra_col_{X.shape[1]}'] = 0.5
            X = X.iloc[:, :7]
            X.columns = important_features
        
        return X

    def _ensure_series(self, data: pd.DataFrame, column: str, default_value=0) -> pd.Series:
        """
        Helper method to ensure a column value is always a Series with correct index.
        Handles both single-row and multi-row DataFrames consistently.
        """
        n_rows = len(data.index)
        
        if column in data.columns:
            val = data[column]
            if isinstance(val, pd.Series):
                # Ensure the Series has the correct index and length
                if len(val) != n_rows:
                    # Reindex to match data.index, filling with the first value or default
                    first_val = val.iloc[0] if len(val) > 0 else default_value
                    return pd.Series([first_val] * n_rows, index=data.index)
                return val
            else:
                # Scalar value - broadcast to Series
                return pd.Series([val] * n_rows, index=data.index)
        else:
            # Column doesn't exist - return Series with default value
            return pd.Series([default_value] * n_rows, index=data.index)

    def _create_basic_features(self, data: pd.DataFrame, sport_key: str) -> pd.DataFrame:
        """
        Create basic statistical features
        """
        # Build dictionary of all basic features to add at once
        basic_features = {}
        n_rows = len(data.index)
        
        # Win/loss records - use helper method for consistency
        home_wins = self._ensure_series(data, 'home_wins', 0)
        home_losses = self._ensure_series(data, 'home_losses', 0)
        away_wins = self._ensure_series(data, 'away_wins', 0)
        away_losses = self._ensure_series(data, 'away_losses', 0)
        
        basic_features['home_win_pct'] = home_wins / (home_wins + home_losses + 1e-6)
        basic_features['away_win_pct'] = away_wins / (away_wins + away_losses + 1e-6)
        
        # Recent form (last 5 games)
        home_recent_wins = self._ensure_series(data, 'home_recent_wins', 0)
        away_recent_wins = self._ensure_series(data, 'away_recent_wins', 0)
        basic_features['home_recent_form'] = home_recent_wins / 5.0
        basic_features['away_recent_form'] = away_recent_wins / 5.0
        
        # Point/goal differentials - handle all sports with proper column mapping
        if sport_key in ['basketball_nba', 'basketball_ncaa', 'americanfootball_nfl']:
            # Use points for basketball and football
            home_points_for = self._ensure_series(data, 'home_points_for', 0)
            home_points_against = self._ensure_series(data, 'home_points_against', 0)
            away_points_for = self._ensure_series(data, 'away_points_for', 0)
            away_points_against = self._ensure_series(data, 'away_points_against', 0)
            
            home_point_diff = home_points_for - home_points_against
            away_point_diff = away_points_for - away_points_against
            basic_features['home_point_diff'] = home_point_diff
            basic_features['away_point_diff'] = away_point_diff
            basic_features['point_diff_diff'] = home_point_diff - away_point_diff
        elif sport_key in ['icehockey_nhl']:
            # NHL uses goals
            home_goals_for = self._ensure_series(data, 'home_goals_for', 0)
            home_goals_against = self._ensure_series(data, 'home_goals_against', 0)
            away_goals_for = self._ensure_series(data, 'away_goals_for', 0)
            away_goals_against = self._ensure_series(data, 'away_goals_against', 0)
            
            home_goal_diff = home_goals_for - home_goals_against
            away_goal_diff = away_goals_for - away_goals_against
            basic_features['home_goal_diff'] = home_goal_diff
            basic_features['away_goal_diff'] = away_goal_diff
            basic_features['goal_diff_diff'] = home_goal_diff - away_goal_diff
        elif sport_key == 'baseball_mlb':
            # MLB uses runs
            home_runs_scored = self._ensure_series(data, 'home_runs_scored', 0)
            home_runs_allowed = self._ensure_series(data, 'home_runs_allowed', 0)
            away_runs_scored = self._ensure_series(data, 'away_runs_scored', 0)
            away_runs_allowed = self._ensure_series(data, 'away_runs_allowed', 0)
            
            home_run_diff = home_runs_scored - home_runs_allowed
            away_run_diff = away_runs_scored - away_runs_allowed
            basic_features['home_run_diff'] = home_run_diff
            basic_features['away_run_diff'] = away_run_diff
            basic_features['run_diff_diff'] = home_run_diff - away_run_diff
        elif sport_key.startswith('soccer_'):
            # Soccer uses goals from different column names
            home_goals_for = self._ensure_series(data, 'home_goals_for', 0)
            home_goals_against = self._ensure_series(data, 'home_goals_against', 0)
            away_goals_for = self._ensure_series(data, 'away_goals_for', 0)
            away_goals_against = self._ensure_series(data, 'away_goals_against', 0)
            
            home_goal_diff = home_goals_for - home_goals_against
            away_goal_diff = away_goals_for - away_goals_against
            basic_features['home_goal_diff'] = home_goal_diff
            basic_features['away_goal_diff'] = away_goal_diff
            basic_features['goal_diff_diff'] = home_goal_diff - away_goal_diff
        
        # Strength of schedule
        basic_features['home_sos'] = self._ensure_series(data, 'home_opponent_win_pct', 0.5)
        basic_features['away_sos'] = self._ensure_series(data, 'away_opponent_win_pct', 0.5)
        
        # Add all basic features at once using pd.concat to prevent fragmentation
        if basic_features:
            new_cols_df = pd.DataFrame(basic_features, index=data.index)
            data = pd.concat([data, new_cols_df], axis=1)
        
        return data

    def _create_sport_specific_features(self, data: pd.DataFrame, sport_key: str) -> pd.DataFrame:
        """
        Create sport-specific advanced metrics
        """
        if sport_key == 'basketball_nba':
            data = self._create_nba_features(data)
        elif sport_key == 'basketball_ncaa':
            data = self._create_ncaa_features(data)
        elif sport_key == 'americanfootball_nfl':
            data = self._create_nfl_features(data)
        elif sport_key == 'baseball_mlb':
            data = self._create_mlb_features(data)
        elif sport_key == 'icehockey_nhl':
            data = self._create_nhl_features(data)
        elif sport_key == 'soccer_epl':
            data = self._create_soccer_features(data)
        
        return data

    def _create_nba_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create NBA-specific advanced metrics
        """
        n_rows = len(data.index)
        
        # Pace and efficiency - use _ensure_series for consistency
        home_poss = self._ensure_series(data, 'home_possessions_per_game', 100)
        away_poss = self._ensure_series(data, 'away_possessions_per_game', 100)
        
        data['home_pace'] = home_poss
        data['away_pace'] = away_poss
        data['pace_diff'] = data['home_pace'] - data['away_pace']
        
        home_points_for = self._ensure_series(data, 'home_points_for', 110)
        away_points_for = self._ensure_series(data, 'away_points_for', 110)
        home_points_against = self._ensure_series(data, 'home_points_against', 110)
        away_points_against = self._ensure_series(data, 'away_points_against', 110)
        
        data['home_off_rating'] = (home_points_for / home_poss) * 100
        data['away_off_rating'] = (away_points_for / away_poss) * 100
        data['home_def_rating'] = (home_points_against / home_poss) * 100
        data['away_def_rating'] = (away_points_against / away_poss) * 100
        
        data['off_rating_diff'] = data['home_off_rating'] - data['away_off_rating']
        data['def_rating_diff'] = data['away_def_rating'] - data['home_def_rating']
        data['net_rating_diff'] = (data['home_off_rating'] - data['home_def_rating']) - (data['away_off_rating'] - data['away_def_rating'])
        
        # Shooting efficiency
        home_fg_made = self._ensure_series(data, 'home_fg_made', 40)
        home_three_made = self._ensure_series(data, 'home_three_made', 12)
        home_fg_attempted = self._ensure_series(data, 'home_fg_attempted', 85)
        home_ft_attempted = self._ensure_series(data, 'home_ft_attempted', 20)
        away_fg_made = self._ensure_series(data, 'away_fg_made', 40)
        away_three_made = self._ensure_series(data, 'away_three_made', 12)
        away_fg_attempted = self._ensure_series(data, 'away_fg_attempted', 85)
        away_ft_attempted = self._ensure_series(data, 'away_ft_attempted', 20)
        
        data['home_efg_pct'] = (home_fg_made + 0.5 * home_three_made) / (home_fg_attempted + 1e-6)
        data['away_efg_pct'] = (away_fg_made + 0.5 * away_three_made) / (away_fg_attempted + 1e-6)
        data['efg_diff'] = data['home_efg_pct'] - data['away_efg_pct']
        
        data['home_ts_pct'] = home_points_for / (2 * (home_fg_attempted + 0.44 * home_ft_attempted) + 1e-6)
        data['away_ts_pct'] = away_points_for / (2 * (away_fg_attempted + 0.44 * away_ft_attempted) + 1e-6)
        data['ts_diff'] = data['home_ts_pct'] - data['away_ts_pct']
        
        # Rebounding
        home_rebounds = self._ensure_series(data, 'home_rebounds', 44)
        away_rebounds = self._ensure_series(data, 'away_rebounds', 44)
        total_rebounds = home_rebounds + away_rebounds
        
        data['home_reb_pct'] = home_rebounds / (total_rebounds + 1e-6)
        data['away_reb_pct'] = away_rebounds / (total_rebounds + 1e-6)
        data['reb_pct_diff'] = data['home_reb_pct'] - data['away_reb_pct']
        
        # Turnovers and assists
        home_turnovers = self._ensure_series(data, 'home_turnovers', 14)
        away_turnovers = self._ensure_series(data, 'away_turnovers', 14)
        home_assists = self._ensure_series(data, 'home_assists', 25)
        away_assists = self._ensure_series(data, 'away_assists', 25)
        
        data['home_tov_pct'] = home_turnovers / (home_poss + 1e-6)
        data['away_tov_pct'] = away_turnovers / (away_poss + 1e-6)
        data['tov_pct_diff'] = data['away_tov_pct'] - data['home_tov_pct']
        
        data['home_ast_pct'] = home_assists / (home_fg_made + 1e-6)
        data['away_ast_pct'] = away_assists / (away_fg_made + 1e-6)
        data['ast_pct_diff'] = data['home_ast_pct'] - data['away_ast_pct']
        
        # Three point shooting
        home_three_attempted = self._ensure_series(data, 'home_three_attempted', 35)
        away_three_attempted = self._ensure_series(data, 'away_three_attempted', 35)
        home_three_made = self._ensure_series(data, 'home_three_made', 12)
        away_three_made = self._ensure_series(data, 'away_three_made', 12)
        
        data['home_three_rate'] = home_three_attempted / (home_fg_attempted + 1e-6)
        data['away_three_rate'] = away_three_attempted / (away_fg_attempted + 1e-6)
        data['three_rate_diff'] = data['home_three_rate'] - data['away_three_rate']
        
        data['home_three_pct'] = home_three_made / (home_three_attempted + 1e-6)
        data['away_three_pct'] = away_three_made / (away_three_attempted + 1e-6)
        data['three_pct_diff'] = data['home_three_pct'] - data['away_three_pct']
        
        return data

    def _create_ncaa_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create NCAA Basketball-specific advanced metrics
        Similar to NBA but with college-specific adjustments
        """
        n_rows = len(data.index)
        
        # Pace and efficiency - use _ensure_series for consistency
        home_poss = self._ensure_series(data, 'home_possessions_per_game', 70)
        away_poss = self._ensure_series(data, 'away_possessions_per_game', 70)
        
        data['home_pace'] = home_poss
        data['away_pace'] = away_poss
        data['pace_diff'] = data['home_pace'] - data['away_pace']
        
        home_points_for = self._ensure_series(data, 'home_points_for', 75)
        away_points_for = self._ensure_series(data, 'away_points_for', 75)
        home_points_against = self._ensure_series(data, 'home_points_against', 75)
        away_points_against = self._ensure_series(data, 'away_points_against', 75)
        
        data['home_off_rating'] = (home_points_for / home_poss) * 100
        data['away_off_rating'] = (away_points_for / away_poss) * 100
        data['home_def_rating'] = (home_points_against / home_poss) * 100
        data['away_def_rating'] = (away_points_against / away_poss) * 100
        
        data['off_rating_diff'] = data['home_off_rating'] - data['away_off_rating']
        data['def_rating_diff'] = data['away_def_rating'] - data['home_def_rating']
        data['net_rating_diff'] = (data['home_off_rating'] - data['home_def_rating']) - (data['away_off_rating'] - data['away_def_rating'])
        
        # Shooting efficiency
        home_fg_made = self._ensure_series(data, 'home_fg_made', 28)
        home_three_made = self._ensure_series(data, 'home_three_made', 8)
        home_fg_attempted = self._ensure_series(data, 'home_fg_attempted', 60)
        home_ft_attempted = self._ensure_series(data, 'home_ft_attempted', 15)
        away_fg_made = self._ensure_series(data, 'away_fg_made', 28)
        away_three_made = self._ensure_series(data, 'away_three_made', 8)
        away_fg_attempted = self._ensure_series(data, 'away_fg_attempted', 60)
        away_ft_attempted = self._ensure_series(data, 'away_ft_attempted', 15)
        
        data['home_efg_pct'] = (home_fg_made + 0.5 * home_three_made) / (home_fg_attempted + 1e-6)
        data['away_efg_pct'] = (away_fg_made + 0.5 * away_three_made) / (away_fg_attempted + 1e-6)
        data['efg_diff'] = data['home_efg_pct'] - data['away_efg_pct']
        
        data['home_ts_pct'] = home_points_for / (2 * (home_fg_attempted + 0.44 * home_ft_attempted) + 1e-6)
        data['away_ts_pct'] = away_points_for / (2 * (away_fg_attempted + 0.44 * away_ft_attempted) + 1e-6)
        data['ts_diff'] = data['home_ts_pct'] - data['away_ts_pct']
        
        # Rebounding
        home_rebounds = self._ensure_series(data, 'home_rebounds', 35)
        away_rebounds = self._ensure_series(data, 'away_rebounds', 35)
        total_rebounds = home_rebounds + away_rebounds
        
        data['home_reb_pct'] = home_rebounds / (total_rebounds + 1e-6)
        data['away_reb_pct'] = away_rebounds / (total_rebounds + 1e-6)
        data['reb_pct_diff'] = data['home_reb_pct'] - data['away_reb_pct']
        
        # Turnovers and assists
        home_turnovers = self._ensure_series(data, 'home_turnovers', 12)
        away_turnovers = self._ensure_series(data, 'away_turnovers', 12)
        home_assists = self._ensure_series(data, 'home_assists', 14)
        away_assists = self._ensure_series(data, 'away_assists', 14)
        
        data['home_tov_pct'] = home_turnovers / (home_poss + 1e-6)
        data['away_tov_pct'] = away_turnovers / (away_poss + 1e-6)
        data['tov_pct_diff'] = data['away_tov_pct'] - data['home_tov_pct']
        
        data['home_ast_pct'] = home_assists / (home_fg_made + 1e-6)
        data['away_ast_pct'] = away_assists / (away_fg_made + 1e-6)
        data['ast_pct_diff'] = data['home_ast_pct'] - data['away_ast_pct']
        
        # Three point shooting
        home_three_attempted = self._ensure_series(data, 'home_three_attempted', 22)
        away_three_attempted = self._ensure_series(data, 'away_three_attempted', 22)
        home_three_made = self._ensure_series(data, 'home_three_made', 8)
        away_three_made = self._ensure_series(data, 'away_three_made', 8)
        
        data['home_three_rate'] = home_three_attempted / (home_fg_attempted + 1e-6)
        data['away_three_rate'] = away_three_attempted / (away_fg_attempted + 1e-6)
        data['three_rate_diff'] = data['home_three_rate'] - data['away_three_rate']
        
        data['home_three_pct'] = home_three_made / (home_three_attempted + 1e-6)
        data['away_three_pct'] = away_three_made / (away_three_attempted + 1e-6)
        data['three_pct_diff'] = data['home_three_pct'] - data['away_three_pct']
        
        return data

    def _create_nfl_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create NFL-specific advanced metrics
        """
        n_rows = len(data.index)
        
        # Offensive efficiency - use _ensure_series for consistency
        home_total_yards = self._ensure_series(data, 'home_total_yards', 350)
        away_total_yards = self._ensure_series(data, 'away_total_yards', 350)
        home_plays = self._ensure_series(data, 'home_plays', 60)
        away_plays = self._ensure_series(data, 'away_plays', 60)
        
        data['home_yards_per_play'] = home_total_yards / home_plays
        data['away_yards_per_play'] = away_total_yards / away_plays
        data['yards_per_play_diff'] = data['home_yards_per_play'] - data['away_yards_per_play']
        
        home_points_for = self._ensure_series(data, 'home_points_for', 22)
        away_points_for = self._ensure_series(data, 'away_points_for', 22)
        home_drives = self._ensure_series(data, 'home_drives', 12)
        away_drives = self._ensure_series(data, 'away_drives', 12)
        data['home_points_per_drive'] = home_points_for / home_drives
        data['away_points_per_drive'] = away_points_for / away_drives
        data['points_per_drive_diff'] = data['home_points_per_drive'] - data['away_points_per_drive']
        
        # Passing efficiency
        home_passing_yards = self._ensure_series(data, 'home_passing_yards', 250)
        home_sack_yards = self._ensure_series(data, 'home_sack_yards', 20)
        home_pass_attempts = self._ensure_series(data, 'home_pass_attempts', 40)
        home_sacks = self._ensure_series(data, 'home_sacks', 3)
        away_passing_yards = self._ensure_series(data, 'away_passing_yards', 250)
        away_sack_yards = self._ensure_series(data, 'away_sack_yards', 20)
        away_pass_attempts = self._ensure_series(data, 'away_pass_attempts', 40)
        away_sacks = self._ensure_series(data, 'away_sacks', 3)
        data['home_net_ypa'] = (home_passing_yards - home_sack_yards) / (home_pass_attempts + home_sacks)
        data['away_net_ypa'] = (away_passing_yards - away_sack_yards) / (away_pass_attempts + away_sacks)
        data['net_ypa_diff'] = data['home_net_ypa'] - data['away_net_ypa']
        
        home_interceptions = self._ensure_series(data, 'home_interceptions', 1)
        away_interceptions = self._ensure_series(data, 'away_interceptions', 1)
        data['home_int_rate'] = home_interceptions / home_pass_attempts
        data['away_int_rate'] = away_interceptions / away_pass_attempts
        data['int_rate_diff'] = data['away_int_rate'] - data['home_int_rate']
        
        # Rushing efficiency
        home_rushing_yards = self._ensure_series(data, 'home_rushing_yards', 120)
        away_rushing_yards = self._ensure_series(data, 'away_rushing_yards', 120)
        home_rush_attempts = self._ensure_series(data, 'home_rush_attempts', 28)
        away_rush_attempts = self._ensure_series(data, 'away_rush_attempts', 28)
        data['home_yards_per_carry'] = home_rushing_yards / home_rush_attempts
        data['away_yards_per_carry'] = away_rushing_yards / away_rush_attempts
        data['yards_per_carry_diff'] = data['home_yards_per_carry'] - data['away_yards_per_carry']
        
        # Turnovers and sacks
        home_turnovers = self._ensure_series(data, 'home_turnovers', 1.5)
        away_turnovers = self._ensure_series(data, 'away_turnovers', 1.5)
        data['home_turnover_rate'] = home_turnovers / home_plays
        data['away_turnover_rate'] = away_turnovers / away_plays
        data['turnover_rate_diff'] = data['away_turnover_rate'] - data['home_turnover_rate']
        
        data['home_sack_rate'] = home_sacks / home_pass_attempts
        data['away_sack_rate'] = away_sacks / away_pass_attempts
        data['sack_rate_diff'] = data['home_sack_rate'] - data['away_sack_rate']
        
        # Third down efficiency
        home_third_down_conversions = self._ensure_series(data, 'home_third_down_conversions', 6)
        home_third_down_attempts = self._ensure_series(data, 'home_third_down_attempts', 14)
        away_third_down_conversions = self._ensure_series(data, 'away_third_down_conversions', 6)
        away_third_down_attempts = self._ensure_series(data, 'away_third_down_attempts', 14)
        data['home_third_down_pct'] = home_third_down_conversions / home_third_down_attempts
        data['away_third_down_pct'] = away_third_down_conversions / away_third_down_attempts
        data['third_down_pct_diff'] = data['home_third_down_pct'] - data['away_third_down_pct']
        
        # Red zone efficiency
        home_red_zone_touchdowns = self._ensure_series(data, 'home_red_zone_touchdowns', 3)
        home_red_zone_attempts = self._ensure_series(data, 'home_red_zone_attempts', 4)
        away_red_zone_touchdowns = self._ensure_series(data, 'away_red_zone_touchdowns', 3)
        away_red_zone_attempts = self._ensure_series(data, 'away_red_zone_attempts', 4)
        data['home_red_zone_pct'] = home_red_zone_touchdowns / home_red_zone_attempts
        data['away_red_zone_pct'] = away_red_zone_touchdowns / away_red_zone_attempts
        data['red_zone_pct_diff'] = data['home_red_zone_pct'] - data['away_red_zone_pct']
        
        return data

    def _create_mlb_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create MLB-specific advanced metrics
        """
        n_rows = len(data.index)
        
        # Batting statistics
        home_hits = self._ensure_series(data, 'home_hits', 8)
        home_walks = self._ensure_series(data, 'home_walks', 3)
        home_hit_by_pitch = self._ensure_series(data, 'home_hit_by_pitch', 0.5)
        home_at_bats = self._ensure_series(data, 'home_at_bats', 34)
        home_sacrifice_flies = self._ensure_series(data, 'home_sacrifice_flies', 0.5)
        away_hits = self._ensure_series(data, 'away_hits', 8)
        away_walks = self._ensure_series(data, 'away_walks', 3)
        away_hit_by_pitch = self._ensure_series(data, 'away_hit_by_pitch', 0.5)
        away_at_bats = self._ensure_series(data, 'away_at_bats', 34)
        away_sacrifice_flies = self._ensure_series(data, 'away_sacrifice_flies', 0.5)
        
        data['home_obp'] = (home_hits + home_walks + home_hit_by_pitch) / (home_at_bats + home_walks + home_hit_by_pitch + home_sacrifice_flies)
        data['away_obp'] = (away_hits + away_walks + away_hit_by_pitch) / (away_at_bats + away_walks + away_hit_by_pitch + away_sacrifice_flies)
        data['obp_diff'] = data['home_obp'] - data['away_obp']
        
        home_singles = self._ensure_series(data, 'home_singles', 5)
        home_doubles = self._ensure_series(data, 'home_doubles', 2)
        home_triples = self._ensure_series(data, 'home_triples', 0.3)
        home_home_runs = self._ensure_series(data, 'home_home_runs', 1.2)
        away_singles = self._ensure_series(data, 'away_singles', 5)
        away_doubles = self._ensure_series(data, 'away_doubles', 2)
        away_triples = self._ensure_series(data, 'away_triples', 0.3)
        away_home_runs = self._ensure_series(data, 'away_home_runs', 1.2)
        
        data['home_slg'] = (home_singles + 2 * home_doubles + 3 * home_triples + 4 * home_home_runs) / home_at_bats
        data['away_slg'] = (away_singles + 2 * away_doubles + 3 * away_triples + 4 * away_home_runs) / away_at_bats
        data['slg_diff'] = data['home_slg'] - data['away_slg']
        
        data['home_ops'] = data['home_obp'] + data['home_slg']
        data['away_ops'] = data['away_obp'] + data['away_slg']
        data['ops_diff'] = data['home_ops'] - data['away_ops']
        
        # Pitching statistics
        home_earned_runs = self._ensure_series(data, 'home_earned_runs', 4)
        home_innings_pitched = self._ensure_series(data, 'home_innings_pitched', 9)
        away_earned_runs = self._ensure_series(data, 'away_earned_runs', 4)
        away_innings_pitched = self._ensure_series(data, 'away_innings_pitched', 9)
        
        data['home_era'] = (home_earned_runs * 9) / home_innings_pitched
        data['away_era'] = (away_earned_runs * 9) / away_innings_pitched
        data['era_diff'] = data['away_era'] - data['home_era']  # Lower is better
        
        data['home_whip'] = (home_walks + home_hits) / home_innings_pitched
        data['away_whip'] = (away_walks + away_hits) / away_innings_pitched
        data['whip_diff'] = data['away_whip'] - data['home_whip']
        
        home_strikeouts = self._ensure_series(data, 'home_strikeouts', 8)
        away_strikeouts = self._ensure_series(data, 'away_strikeouts', 8)
        
        data['home_k_rate'] = home_strikeouts / home_at_bats
        data['away_k_rate'] = away_strikeouts / away_at_bats
        data['k_rate_diff'] = data['home_k_rate'] - data['away_k_rate']
        
        data['home_bb_rate'] = home_walks / home_at_bats
        data['away_bb_rate'] = away_walks / away_at_bats
        data['bb_rate_diff'] = data['away_bb_rate'] - data['home_bb_rate']
        
        # Fielding statistics
        home_putouts = self._ensure_series(data, 'home_putouts', 27)
        home_assists = self._ensure_series(data, 'home_assists', 12)
        home_errors = self._ensure_series(data, 'home_errors', 0.8)
        away_putouts = self._ensure_series(data, 'away_putouts', 27)
        away_assists = self._ensure_series(data, 'away_assists', 12)
        away_errors = self._ensure_series(data, 'away_errors', 0.8)
        
        data['home_fielding_pct'] = (home_putouts + home_assists) / (home_putouts + home_assists + home_errors)
        data['away_fielding_pct'] = (away_putouts + away_assists) / (away_putouts + away_assists + away_errors)
        data['fielding_pct_diff'] = data['home_fielding_pct'] - data['away_fielding_pct']
        
        # Advanced statistics
        data['home_babip'] = (home_hits - home_home_runs) / (home_at_bats - home_strikeouts - home_home_runs + home_sacrifice_flies)
        data['away_babip'] = (away_hits - away_home_runs) / (away_at_bats - away_strikeouts - away_home_runs + away_sacrifice_flies)
        data['babip_diff'] = data['home_babip'] - data['away_babip']
        
        return data

    def _create_nhl_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create NHL-specific advanced metrics
        """
        n_rows = len(data.index)
        
        # Goals and expected goals - use _ensure_series for consistency
        home_time_on_ice = self._ensure_series(data, 'home_time_on_ice', 3600)
        away_time_on_ice = self._ensure_series(data, 'away_time_on_ice', 3600)
        home_goals_for = self._ensure_series(data, 'home_goals_for', 3)
        away_goals_for = self._ensure_series(data, 'away_goals_for', 3)
        home_expected_goals_for = self._ensure_series(data, 'home_expected_goals_for', 3)
        away_expected_goals_for = self._ensure_series(data, 'away_expected_goals_for', 3)
        
        data['home_goals_per_60'] = (home_goals_for * 60) / home_time_on_ice
        data['away_goals_per_60'] = (away_goals_for * 60) / away_time_on_ice
        data['goals_per_60_diff'] = data['home_goals_per_60'] - data['away_goals_per_60']
        
        data['home_xg_per_60'] = (home_expected_goals_for * 60) / home_time_on_ice
        data['away_xg_per_60'] = (away_expected_goals_for * 60) / away_time_on_ice
        data['xg_per_60_diff'] = data['home_xg_per_60'] - data['away_xg_per_60']
        
        # Shooting and save percentages
        home_shots_on_goal = self._ensure_series(data, 'home_shots_on_goal', 30)
        away_shots_on_goal = self._ensure_series(data, 'away_shots_on_goal', 30)
        home_goals_against = self._ensure_series(data, 'home_goals_against', 3)
        away_goals_against = self._ensure_series(data, 'away_goals_against', 3)
        home_shots_against = self._ensure_series(data, 'home_shots_against', 30)
        away_shots_against = self._ensure_series(data, 'away_shots_against', 30)
        
        data['home_shooting_pct'] = home_goals_for / home_shots_on_goal
        data['away_shooting_pct'] = away_goals_for / away_shots_on_goal
        data['shooting_pct_diff'] = data['home_shooting_pct'] - data['away_shooting_pct']
        
        data['home_save_pct'] = 1 - (home_goals_against / home_shots_against)
        data['away_save_pct'] = 1 - (away_goals_against / away_shots_against)
        data['save_pct_diff'] = data['home_save_pct'] - data['away_save_pct']
        
        # Corsi and Fenwick (possession metrics)
        home_missed_shots = self._ensure_series(data, 'home_missed_shots', 12)
        home_blocked_shots_against = self._ensure_series(data, 'home_blocked_shots_against', 15)
        home_missed_shots_against = self._ensure_series(data, 'home_missed_shots_against', 12)
        home_blocked_shots = self._ensure_series(data, 'home_blocked_shots', 15)
        away_missed_shots = self._ensure_series(data, 'away_missed_shots', 12)
        away_blocked_shots_against = self._ensure_series(data, 'away_blocked_shots_against', 15)
        away_missed_shots_against = self._ensure_series(data, 'away_missed_shots_against', 12)
        away_blocked_shots = self._ensure_series(data, 'away_blocked_shots', 15)
        
        data['home_corsi_for'] = home_shots_on_goal + home_missed_shots + home_blocked_shots_against
        data['home_corsi_against'] = home_shots_against + home_missed_shots_against + home_blocked_shots
        data['home_corsi_pct'] = data['home_corsi_for'] / (data['home_corsi_for'] + data['home_corsi_against'])
        
        data['away_corsi_for'] = away_shots_on_goal + away_missed_shots + away_blocked_shots_against
        data['away_corsi_against'] = away_shots_against + away_missed_shots_against + away_blocked_shots
        data['away_corsi_pct'] = data['away_corsi_for'] / (data['away_corsi_for'] + data['away_corsi_against'])
        
        data['corsi_pct_diff'] = data['home_corsi_pct'] - data['away_corsi_pct']
        
        # Fenwick (unblocked shot attempts)
        data['home_fenwick_for'] = home_shots_on_goal + home_missed_shots
        data['home_fenwick_against'] = home_shots_against + home_missed_shots_against
        data['home_fenwick_pct'] = data['home_fenwick_for'] / (data['home_fenwick_for'] + data['home_fenwick_against'])
        
        data['away_fenwick_for'] = away_shots_on_goal + away_missed_shots
        data['away_fenwick_against'] = away_shots_against + away_missed_shots_against
        data['away_fenwick_pct'] = data['away_fenwick_for'] / (data['away_fenwick_for'] + data['away_fenwick_against'])
        
        data['fenwick_pct_diff'] = data['home_fenwick_pct'] - data['away_fenwick_pct']
        
        # Special teams
        home_power_play_goals = self._ensure_series(data, 'home_power_play_goals', 0.8)
        home_power_play_opportunities = self._ensure_series(data, 'home_power_play_opportunities', 3)
        away_power_play_goals = self._ensure_series(data, 'away_power_play_goals', 0.8)
        away_power_play_opportunities = self._ensure_series(data, 'away_power_play_opportunities', 3)
        home_power_play_goals_against = self._ensure_series(data, 'home_power_play_goals_against', 0.8)
        home_penalty_kill_opportunities = self._ensure_series(data, 'home_penalty_kill_opportunities', 3)
        away_power_play_goals_against = self._ensure_series(data, 'away_power_play_goals_against', 0.8)
        away_penalty_kill_opportunities = self._ensure_series(data, 'away_penalty_kill_opportunities', 3)
        
        data['home_pp_pct'] = home_power_play_goals / home_power_play_opportunities
        data['away_pp_pct'] = away_power_play_goals / away_power_play_opportunities
        data['pp_pct_diff'] = data['home_pp_pct'] - data['away_pp_pct']
        
        data['home_pk_pct'] = 1 - (home_power_play_goals_against / home_penalty_kill_opportunities)
        data['away_pk_pct'] = 1 - (away_power_play_goals_against / away_penalty_kill_opportunities)
        data['pk_pct_diff'] = data['home_pk_pct'] - data['away_pk_pct']
        
        return data

    def _create_soccer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create soccer-specific advanced metrics
        """
        n_rows = len(data.index)
        
        # Goals and expected goals - use _ensure_series for consistency
        home_goals_for = self._ensure_series(data, 'home_goals_for', 0)
        home_matches_played = self._ensure_series(data, 'home_matches_played', 1)
        away_goals_for = self._ensure_series(data, 'away_goals_for', 0)
        away_matches_played = self._ensure_series(data, 'away_matches_played', 1)
        
        data['home_goals_per_match'] = home_goals_for / home_matches_played
        data['away_goals_per_match'] = away_goals_for / away_matches_played
        data['goals_per_match_diff'] = data['home_goals_per_match'] - data['away_goals_per_match']
        
        home_expected_goals = self._ensure_series(data, 'home_expected_goals', 0)
        away_expected_goals = self._ensure_series(data, 'away_expected_goals', 0)
        
        data['home_xg_per_match'] = home_expected_goals / home_matches_played
        data['away_xg_per_match'] = away_expected_goals / away_matches_played
        data['xg_per_match_diff'] = data['home_xg_per_match'] - data['away_xg_per_match']
        
        # Goals against
        home_goals_against = self._ensure_series(data, 'home_goals_against', 0)
        away_goals_against = self._ensure_series(data, 'away_goals_against', 0)
        
        data['home_goals_against_per_match'] = home_goals_against / home_matches_played
        data['away_goals_against_per_match'] = away_goals_against / away_matches_played
        data['goals_against_per_match_diff'] = data['away_goals_against_per_match'] - data['home_goals_against_per_match']
        
        # Shooting
        home_shots = self._ensure_series(data, 'home_shots', 1)
        away_shots = self._ensure_series(data, 'away_shots', 1)
        
        data['home_shots_per_match'] = home_shots / home_matches_played
        data['away_shots_per_match'] = away_shots / away_matches_played
        data['shots_per_match_diff'] = data['home_shots_per_match'] - data['away_shots_per_match']
        
        data['home_shot_conversion'] = home_goals_for / home_shots
        data['away_shot_conversion'] = away_goals_for / away_shots
        data['shot_conversion_diff'] = data['home_shot_conversion'] - data['away_shot_conversion']
        
        # Possession and passing
        home_possession_pct = self._ensure_series(data, 'home_possession_pct', 50)
        away_possession_pct = self._ensure_series(data, 'away_possession_pct', 50)
        home_pass_completion_pct = self._ensure_series(data, 'home_pass_completion_pct', 75)
        away_pass_completion_pct = self._ensure_series(data, 'away_pass_completion_pct', 75)
        
        data['possession_diff'] = home_possession_pct - away_possession_pct
        data['pass_completion_diff'] = home_pass_completion_pct - away_pass_completion_pct
        
        # Discipline
        home_yellow_cards = self._ensure_series(data, 'home_yellow_cards', 0)
        away_yellow_cards = self._ensure_series(data, 'away_yellow_cards', 0)
        
        data['home_cards_per_match'] = home_yellow_cards / home_matches_played
        data['away_cards_per_match'] = away_yellow_cards / away_matches_played
        data['cards_per_match_diff'] = data['away_cards_per_match'] - data['home_cards_per_match']
        
        # Clean sheets
        home_clean_sheets = self._ensure_series(data, 'home_clean_sheets', 0)
        away_clean_sheets = self._ensure_series(data, 'away_clean_sheets', 0)
        
        data['home_clean_sheet_pct'] = home_clean_sheets / home_matches_played
        data['away_clean_sheet_pct'] = away_clean_sheets / away_matches_played
        data['clean_sheet_pct_diff'] = data['home_clean_sheet_pct'] - data['away_clean_sheet_pct']
        
        return data

    def _create_contextual_features(self, data: pd.DataFrame, sport_key: str) -> pd.DataFrame:
        """
        Create contextual features like home/away splits, rest days, etc.
        """
        # Build dictionary of all contextual features to add at once
        contextual_features = {}
        n_rows = len(data.index)
        
        # Home/away performance splits - use helper method
        home_home_wins = self._ensure_series(data, 'home_home_wins', 0)
        home_home_losses = self._ensure_series(data, 'home_home_losses', 0)
        home_away_wins = self._ensure_series(data, 'home_away_wins', 0)
        home_away_losses = self._ensure_series(data, 'home_away_losses', 0)
        
        home_home_win_pct = home_home_wins / (home_home_wins + home_home_losses + 1e-6)
        home_away_win_pct = home_away_wins / (home_away_wins + home_away_losses + 1e-6)
        contextual_features['home_home_win_pct'] = home_home_win_pct
        contextual_features['home_away_win_pct'] = home_away_win_pct
        contextual_features['home_away_diff'] = home_home_win_pct - home_away_win_pct
        
        away_home_wins = self._ensure_series(data, 'away_home_wins', 0)
        away_home_losses = self._ensure_series(data, 'away_home_losses', 0)
        away_away_wins = self._ensure_series(data, 'away_away_wins', 0)
        away_away_losses = self._ensure_series(data, 'away_away_losses', 0)
        
        away_home_win_pct = away_home_wins / (away_home_wins + away_home_losses + 1e-6)
        away_away_win_pct = away_away_wins / (away_away_wins + away_away_losses + 1e-6)
        contextual_features['away_home_win_pct'] = away_home_win_pct
        contextual_features['away_away_win_pct'] = away_away_win_pct
        contextual_features['away_away_diff'] = away_away_win_pct - away_home_win_pct
        
        # Rest days impact - with safe defaults
        # Use commence_time if game_date is not available
        if 'game_date' not in data.columns and 'commence_time' in data.columns:
            data['game_date'] = data['commence_time']
            
        # If we have date information
        if 'game_date' in data.columns and 'home_last_game_date' in data.columns and 'away_last_game_date' in data.columns:
            try:
                game_date = pd.to_datetime(self._ensure_series(data, 'game_date', 0))
                home_last_date = pd.to_datetime(self._ensure_series(data, 'home_last_game_date', 0))
                away_last_date = pd.to_datetime(self._ensure_series(data, 'away_last_game_date', 0))
                home_rest_days = (game_date - home_last_date).dt.days
                away_rest_days = (game_date - away_last_date).dt.days
            except:
                # Default to standard rest (2 days) if date parsing fails
                home_rest_days = pd.Series([2] * n_rows, index=data.index)
                away_rest_days = pd.Series([2] * n_rows, index=data.index)
        else:
            # Default to standard rest
            home_rest_days = pd.Series([2] * n_rows, index=data.index)
            away_rest_days = pd.Series([2] * n_rows, index=data.index)
            
        contextual_features['home_rest_days'] = home_rest_days
        contextual_features['away_rest_days'] = away_rest_days
        contextual_features['rest_days_diff'] = home_rest_days - away_rest_days
        
        # Back-to-back games
        contextual_features['home_back_to_back'] = (home_rest_days == 1).astype(int)
        contextual_features['away_back_to_back'] = (away_rest_days == 1).astype(int)
        contextual_features['back_to_back_diff'] = contextual_features['home_back_to_back'] - contextual_features['away_back_to_back']
        
        # Travel distance (if available)
        home_travel = self._ensure_series(data, 'home_travel_miles', 0)
        away_travel = self._ensure_series(data, 'away_travel_miles', 0)
        contextual_features['travel_diff'] = home_travel - away_travel
        contextual_features['home_long_travel'] = (home_travel > 1000).astype(int)
        contextual_features['away_long_travel'] = (away_travel > 1000).astype(int)
        
        # Time zone changes
        home_time_zone_change = self._ensure_series(data, 'home_time_zones_traveled', 0)
        away_time_zone_change = self._ensure_series(data, 'away_time_zones_traveled', 0)
        contextual_features['home_time_zone_change'] = home_time_zone_change
        contextual_features['away_time_zone_change'] = away_time_zone_change
        contextual_features['time_zone_diff'] = home_time_zone_change - away_time_zone_change
        
        # Days since last game
        contextual_features['home_days_since_game'] = home_rest_days
        contextual_features['away_days_since_game'] = away_rest_days
        
        # Momentum (recent performance trend)
        home_recent = self._ensure_series(data, 'home_recent_wins', 0)
        home_prev = self._ensure_series(data, 'home_previous_wins', 0)
        away_recent = self._ensure_series(data, 'away_recent_wins', 0)
        away_prev = self._ensure_series(data, 'away_previous_wins', 0)
        
        contextual_features['home_momentum'] = home_recent - home_prev
        contextual_features['away_momentum'] = away_recent - away_prev
        contextual_features['momentum_diff'] = contextual_features['home_momentum'] - contextual_features['away_momentum']
        
        # Add all contextual features at once using pd.concat to prevent fragmentation
        if contextual_features:
            new_cols_df = pd.DataFrame(contextual_features, index=data.index)
            data = pd.concat([data, new_cols_df], axis=1)
        
        return data

    def _create_historical_features(self, data: pd.DataFrame, sport_key: str) -> pd.DataFrame:
        """
        Create historical features like head-to-head records, trends, etc.
        """
        # Build dictionary of all historical features to add at once
        historical_features = {}
        n_rows = len(data.index)
        
        # Head-to-head record - use _ensure_series for consistency
        h2h_home_wins = self._ensure_series(data, 'historical_h2h_home_wins', 0)
        h2h_away_wins = self._ensure_series(data, 'historical_h2h_away_wins', 0)
        historical_features['h2h_home_wins'] = h2h_home_wins
        historical_features['h2h_away_wins'] = h2h_away_wins
        historical_features['h2h_home_pct'] = h2h_home_wins / (h2h_home_wins + h2h_away_wins + 1e-6)
        
        # Recent head-to-head (last 5 meetings)
        recent_h2h_home_wins = self._ensure_series(data, 'recent_h2h_wins_home', 0)
        historical_features['recent_h2h_home_wins'] = recent_h2h_home_wins
        historical_features['recent_h2h_pct'] = recent_h2h_home_wins / 5.0
        
        # Season series (if applicable)
        season_series_home_wins = self._ensure_series(data, 'season_series_home_wins', 0)
        season_series_away_wins = self._ensure_series(data, 'season_series_away_wins', 0)
        historical_features['season_series_home_wins'] = season_series_home_wins
        historical_features['season_series_away_wins'] = season_series_away_wins
        historical_features['season_series_home_pct'] = season_series_home_wins / (season_series_home_wins + season_series_away_wins + 1e-6)
        
        # Performance vs similar opponents
        home_vs_top_wins = self._ensure_series(data, 'home_vs_top_teams_wins', 0)
        home_vs_top_losses = self._ensure_series(data, 'home_vs_top_teams_losses', 0)
        away_vs_top_wins = self._ensure_series(data, 'away_vs_top_teams_wins', 0)
        away_vs_top_losses = self._ensure_series(data, 'away_vs_top_teams_losses', 0)
        home_vs_similar_record = home_vs_top_wins / (home_vs_top_wins + home_vs_top_losses + 1e-6)
        away_vs_similar_record = away_vs_top_wins / (away_vs_top_wins + away_vs_top_losses + 1e-6)
        historical_features['home_vs_similar_record'] = home_vs_similar_record
        historical_features['away_vs_similar_record'] = away_vs_similar_record
        historical_features['vs_similar_diff'] = home_vs_similar_record - away_vs_similar_record
        
        # Trend analysis (moving averages)
        home_recent_form = self._ensure_series(data, 'home_recent_form', 0)
        home_season_form = self._ensure_series(data, 'home_season_form', 0)
        away_recent_form = self._ensure_series(data, 'away_recent_form', 0)
        away_season_form = self._ensure_series(data, 'away_season_form', 0)
        home_form_trend = home_recent_form - home_season_form
        away_form_trend = away_recent_form - away_season_form
        historical_features['home_form_trend'] = home_form_trend
        historical_features['away_form_trend'] = away_form_trend
        historical_features['form_trend_diff'] = home_form_trend - away_form_trend
        
        # Consistency metrics
        home_points_std = self._ensure_series(data, 'home_points_std', 0)
        home_points_mean = self._ensure_series(data, 'home_points_mean', 0)
        away_points_std = self._ensure_series(data, 'away_points_std', 0)
        away_points_mean = self._ensure_series(data, 'away_points_mean', 0)
        home_consistency = home_points_std / (home_points_mean + 1e-6)
        away_consistency = away_points_std / (away_points_mean + 1e-6)
        historical_features['home_consistency'] = home_consistency
        historical_features['away_consistency'] = away_consistency
        historical_features['consistency_diff'] = away_consistency - home_consistency
        
        # Clutch performance (close games)
        home_close_wins = self._ensure_series(data, 'home_close_games_wins', 0)
        home_close_losses = self._ensure_series(data, 'home_close_games_losses', 0)
        away_close_wins = self._ensure_series(data, 'away_close_games_wins', 0)
        away_close_losses = self._ensure_series(data, 'away_close_games_losses', 0)
        home_clutch_record = home_close_wins / (home_close_wins + home_close_losses + 1e-6)
        away_clutch_record = away_close_wins / (away_close_wins + away_close_losses + 1e-6)
        historical_features['home_clutch_record'] = home_clutch_record
        historical_features['away_clutch_record'] = away_clutch_record
        historical_features['clutch_diff'] = home_clutch_record - away_clutch_record
        
        # Add all historical features at once using pd.concat to prevent fragmentation
        if historical_features:
            new_cols_df = pd.DataFrame(historical_features, index=data.index)
            data = pd.concat([data, new_cols_df], axis=1)
        
        return data

    def _create_market_specific_features(self, data: pd.DataFrame, sport_key: str, market_type: str) -> pd.DataFrame:
        """
        Create market-specific features (spread, total, moneyline)
        """
        # Build dictionary of all market-specific features to add at once
        market_features = {}
        n_rows = len(data.index)
        
        if market_type == 'spread':
            # Historical spread performance - use _ensure_series for consistency
            home_ats_wins = self._ensure_series(data, 'home_ats_wins', 0)
            home_ats_losses = self._ensure_series(data, 'home_ats_losses', 0)
            away_ats_wins = self._ensure_series(data, 'away_ats_wins', 0)
            away_ats_losses = self._ensure_series(data, 'away_ats_losses', 0)
            home_ats_record = home_ats_wins / (home_ats_wins + home_ats_losses + 1e-6)
            away_ats_record = away_ats_wins / (away_ats_wins + away_ats_losses + 1e-6)
            market_features['home_ats_record'] = home_ats_record
            market_features['away_ats_record'] = away_ats_record
            market_features['ats_diff'] = home_ats_record - away_ats_record
            
            # Average margin vs spread
            market_features['home_avg_cover_margin'] = self._ensure_series(data, 'home_avg_margin_vs_spread', 0)
            market_features['away_avg_cover_margin'] = self._ensure_series(data, 'away_avg_margin_vs_spread', 0)
            market_features['cover_margin_diff'] = market_features['home_avg_cover_margin'] - market_features['away_avg_cover_margin']
            
            # Recent spread performance
            home_recent_ats_wins = self._ensure_series(data, 'home_recent_ats_wins', 0)
            away_recent_ats_wins = self._ensure_series(data, 'away_recent_ats_wins', 0)
            market_features['home_recent_ats'] = home_recent_ats_wins / 5.0
            market_features['away_recent_ats'] = away_recent_ats_wins / 5.0
            market_features['recent_ats_diff'] = market_features['home_recent_ats'] - market_features['away_recent_ats']
            
        elif market_type == 'total':
            # Historical total performance - use _ensure_series for consistency
            home_over_wins = self._ensure_series(data, 'home_over_wins', 0)
            home_under_wins = self._ensure_series(data, 'home_under_wins', 0)
            away_over_wins = self._ensure_series(data, 'away_over_wins', 0)
            away_under_wins = self._ensure_series(data, 'away_under_wins', 0)
            home_over_record = home_over_wins / (home_over_wins + home_under_wins + 1e-6)
            away_over_record = away_over_wins / (away_over_wins + away_under_wins + 1e-6)
            market_features['home_over_record'] = home_over_record
            market_features['away_over_record'] = away_over_record
            market_features['over_diff'] = home_over_record - away_over_record
            
            # Average total points
            home_points_for = self._ensure_series(data, 'home_points_for', 0)
            home_points_against = self._ensure_series(data, 'home_points_against', 0)
            away_points_for = self._ensure_series(data, 'away_points_for', 0)
            away_points_against = self._ensure_series(data, 'away_points_against', 0)
            home_avg_total = home_points_for + home_points_against
            away_avg_total = away_points_for + away_points_against
            market_features['home_avg_total'] = home_avg_total
            market_features['away_avg_total'] = away_avg_total
            market_features['avg_total_diff'] = home_avg_total - away_avg_total
            
            # Pace factors
            if sport_key == 'basketball_nba':
                home_pace = self._ensure_series(data, 'home_possessions_per_game', 100)
                away_pace = self._ensure_series(data, 'away_possessions_per_game', 100)
                market_features['home_pace_factor'] = home_pace
                market_features['away_pace_factor'] = away_pace
                market_features['pace_factor_diff'] = home_pace - away_pace
            
        elif market_type == 'moneyline':
            # Straight up win percentages - use _ensure_series for consistency
            home_wins = self._ensure_series(data, 'home_wins', 0)
            home_losses = self._ensure_series(data, 'home_losses', 0)
            away_wins = self._ensure_series(data, 'away_wins', 0)
            away_losses = self._ensure_series(data, 'away_losses', 0)
            home_win_pct = home_wins / (home_wins + home_losses + 1e-6)
            away_win_pct = away_wins / (away_wins + away_losses + 1e-6)
            market_features['home_win_pct'] = home_win_pct
            market_features['away_win_pct'] = away_win_pct
            market_features['win_pct_diff'] = home_win_pct - away_win_pct
            
            # Recent form
            home_recent_wins = self._ensure_series(data, 'home_recent_wins', 0)
            away_recent_wins = self._ensure_series(data, 'away_recent_wins', 0)
            market_features['home_recent_win_pct'] = home_recent_wins / 5.0
            market_features['away_recent_win_pct'] = away_recent_wins / 5.0
            market_features['recent_win_pct_diff'] = market_features['home_recent_win_pct'] - market_features['away_recent_win_pct']
        
        # Add all market-specific features at once using pd.concat to prevent fragmentation
        if market_features:
            new_cols_df = pd.DataFrame(market_features, index=data.index)
            data = pd.concat([data, new_cols_df], axis=1)
            
        return data

    def _create_weather_features(self, data: pd.DataFrame, sport_key: str) -> pd.DataFrame:
        """
        Create weather impact features (for outdoor sports)
        """
        if sport_key not in ['americanfootball_nfl', 'baseball_mlb', 'soccer_epl']:
            return data
        
        # Build dictionary of all weather features to add at once
        weather_features = {}
        n_rows = len(data.index)
        
        # Temperature impact - use _ensure_series for consistency
        temperature = self._ensure_series(data, 'temperature', 72)
        weather_features['temp_category'] = pd.cut(temperature, bins=[-50, 32, 50, 70, 90, 150], 
                                       labels=['very_cold', 'cold', 'mild', 'warm', 'hot'])
        weather_features['temp_extreme'] = ((temperature < 32) | (temperature > 90)).astype(int)
        
        # Wind impact - use _ensure_series for consistency
        wind_speed = self._ensure_series(data, 'wind_speed', 5)
        weather_features['wind_speed_category'] = pd.cut(wind_speed, bins=[0, 5, 15, 25, 100], 
                                           labels=['calm', 'moderate', 'strong', 'extreme'])
        weather_features['strong_wind'] = (wind_speed > 15).astype(int)
        
        # Precipitation impact - use _ensure_series for consistency
        precipitation = self._ensure_series(data, 'precipitation', 0)
        weather_features['precipitation_binary'] = (precipitation > 0).astype(int)
        weather_features['heavy_precipitation'] = (precipitation > 0.5).astype(int)
        
        # Combined weather impact
        weather_features['adverse_weather'] = (weather_features['temp_extreme'] | weather_features['strong_wind'] | weather_features['heavy_precipitation']).astype(int)
        
        # Sport-specific weather impacts
        if sport_key == 'baseball_mlb':
            # Wind direction for baseball (affects home run probability)
            wind_direction = self._ensure_series(data, 'wind_direction', 0)
            weather_features['wind_blowing_out'] = ((wind_direction >= 315) | (wind_direction <= 45)).astype(int)
            weather_features['wind_blowing_in'] = ((wind_direction >= 135) & (wind_direction <= 225)).astype(int)
            
        elif sport_key == 'americanfootball_nfl':
            # Cold weather affects passing game
            weather_features['cold_weather_pass_impact'] = (temperature < 40).astype(int)
            # Wind affects kicking game
            weather_features['wind_kicking_impact'] = (wind_speed > 20).astype(int)
            
        elif sport_key == 'soccer_epl':
            # Rain affects ball control and passing
            weather_features['rain_passing_impact'] = (precipitation > 0.1).astype(int)
            # Wind affects long balls and set pieces
            weather_features['wind_set_piece_impact'] = (wind_speed > 15).astype(int)
        
        # Add all weather features at once using pd.concat to prevent fragmentation
        if weather_features:
            new_cols_df = pd.DataFrame(weather_features, index=data.index)
            data = pd.concat([data, new_cols_df], axis=1)
        
        return data

    def _create_injury_features(self, data: pd.DataFrame, sport_key: str) -> pd.DataFrame:
        """
        Create injury impact features
        """
        # Build dictionary of all injury features to add at once
        injury_features = {}
        
        # Basic injury counts - use _ensure_series for consistency
        home_injured = self._ensure_series(data, 'home_injured_players', 0)
        away_injured = self._ensure_series(data, 'away_injured_players', 0)
        injury_features['home_injuries'] = home_injured
        injury_features['away_injuries'] = away_injured
        injury_features['injury_diff'] = home_injured - away_injured
        
        # Key player injuries (weighted by position importance)
        home_star_injured = self._ensure_series(data, 'home_star_players_injured', 0)
        away_star_injured = self._ensure_series(data, 'away_star_players_injured', 0)
        injury_features['home_key_injuries'] = home_star_injured
        injury_features['away_key_injuries'] = away_star_injured
        injury_features['key_injury_diff'] = home_star_injured - away_star_injured
        
        # Injury severity (if available)
        if 'home_avg_injury_severity' in data.columns:
            home_severity = self._ensure_series(data, 'home_avg_injury_severity', 0)
            away_severity = self._ensure_series(data, 'away_avg_injury_severity', 0)
            injury_features['home_injury_severity'] = home_severity
            injury_features['away_injury_severity'] = away_severity
            injury_features['injury_severity_diff'] = home_severity - away_severity
        
        # Position-specific injuries
        if sport_key == 'basketball_nba':
            home_pg = self._ensure_series(data, 'home_point_guard_injured', 0).astype(int)
            home_c = self._ensure_series(data, 'home_center_injured', 0).astype(int)
            away_pg = self._ensure_series(data, 'away_point_guard_injured', 0).astype(int)
            away_c = self._ensure_series(data, 'away_center_injured', 0).astype(int)
            
            injury_features['home_pg_injury'] = home_pg
            injury_features['home_c_injury'] = home_c
            injury_features['home_key_pos_injury'] = home_pg | home_c
            injury_features['away_pg_injury'] = away_pg
            injury_features['away_c_injury'] = away_c
            injury_features['away_key_pos_injury'] = away_pg | away_c
            injury_features['key_pos_injury_diff'] = (home_pg | home_c).astype(int) - (away_pg | away_c).astype(int)
            
        elif sport_key == 'americanfootball_nfl':
            home_qb = self._ensure_series(data, 'home_quarterback_injured', 0).astype(int)
            home_rb = self._ensure_series(data, 'home_running_back_injured', 0).astype(int)
            home_wr = self._ensure_series(data, 'home_wide_receiver_injured', 0).astype(int)
            away_qb = self._ensure_series(data, 'away_quarterback_injured', 0).astype(int)
            away_rb = self._ensure_series(data, 'away_running_back_injured', 0).astype(int)
            away_wr = self._ensure_series(data, 'away_wide_receiver_injured', 0).astype(int)
            
            injury_features['home_qb_injury'] = home_qb
            injury_features['home_rb_injury'] = home_rb
            injury_features['home_wr_injury'] = home_wr
            injury_features['away_qb_injury'] = away_qb
            injury_features['away_rb_injury'] = away_rb
            injury_features['away_wr_injury'] = away_wr
            injury_features['qb_injury_diff'] = home_qb - away_qb
            
        elif sport_key == 'baseball_mlb':
            home_ace = self._ensure_series(data, 'home_ace_pitcher_injured', 0).astype(int)
            home_closer = self._ensure_series(data, 'home_closer_injured', 0).astype(int)
            away_ace = self._ensure_series(data, 'away_ace_pitcher_injured', 0).astype(int)
            away_closer = self._ensure_series(data, 'away_closer_injured', 0).astype(int)
            
            injury_features['home_ace_injury'] = home_ace
            injury_features['home_closer_injury'] = home_closer
            injury_features['away_ace_injury'] = away_ace
            injury_features['away_closer_injury'] = away_closer
            injury_features['pitching_injury_diff'] = home_ace - away_ace
        
        # Injury impact on team performance
        home_impact = self._ensure_series(data, 'home_injury_performance_impact', 0)
        away_impact = self._ensure_series(data, 'away_injury_performance_impact', 0)
        injury_features['home_injury_impact'] = home_impact
        injury_features['away_injury_impact'] = away_impact
        injury_features['injury_impact_diff'] = home_impact - away_impact
        
        # Add all features at once using pd.concat to prevent fragmentation
        if injury_features:
            new_cols_df = pd.DataFrame(injury_features, index=data.index)
            data = pd.concat([data, new_cols_df], axis=1)
        
        return data

    def _create_target_variable(self, data: pd.DataFrame, market_type: str) -> np.ndarray:
        """
        Create target variable based on market type
        """
        n_rows = len(data.index)
        
        # Handle puck_line as spread for NHL
        effective_market_type = 'spread' if market_type == 'puck_line' else market_type
        
        if effective_market_type == 'spread':
            # Home team covers spread (1), doesn't cover (0), push (2)
            home_score = self._ensure_series(data, 'home_score', 0)
            away_score = self._ensure_series(data, 'away_score', 0)
            spread_line = self._ensure_series(data, 'spread_line', 0)
            spread_margin = home_score - away_score + spread_line
            target = np.where(spread_margin > 0, 1, 
                             np.where(spread_margin < 0, 0, 2))
        
        elif effective_market_type == 'total':
            # Over (1), Under (0), push (2)
            home_score = self._ensure_series(data, 'home_score', 0)
            away_score = self._ensure_series(data, 'away_score', 0)
            total_line = self._ensure_series(data, 'total_line', 0)
            total_points = home_score + away_score
            target = np.where(total_points > total_line, 1,
                             np.where(total_points < total_line, 0, 2))
        
        elif effective_market_type == 'moneyline':
            # Home win (1), Away win (0), Draw (2)
            home_score = self._ensure_series(data, 'home_score', 0)
            away_score = self._ensure_series(data, 'away_score', 0)
            target = np.where(home_score > away_score, 1,
                             np.where(home_score < away_score, 0, 2))
        
        else:
            raise ValueError(f"Unknown market type: {market_type}")
        
        return target

    def _select_and_scale_features(self, data: pd.DataFrame, sport_key: str, market_type: str) -> pd.DataFrame:
        """
        Select relevant features and apply scaling
        """
        # Get feature columns (exclude target and non-feature columns)
        exclude_cols = ['target', 'home_score', 'away_score', 'game_date', 'home_team', 'away_team', 
                        'commence_time', 'home_last_game_date', 'away_last_game_date']
        feature_cols = [col for col in data.columns if col not in exclude_cols]
        
        # Select only numeric columns (exclude datetime, object, category types)
        data_features = data[feature_cols].select_dtypes(include=[np.number]).copy()
        
        # Remove columns with all NaN values
        data_features = data_features.dropna(axis=1, how='all')
        
        # Fill remaining NaN values with 0 for numeric columns only
        for col in data_features.columns:
            try:
                # Fill NaN with median, or 0 if all NaN
                col_median = data_features[col].median()
                # Handle both scalar and Series cases
                if isinstance(col_median, pd.Series):
                    col_median = col_median.iloc[0] if len(col_median) > 0 else 0
                if pd.isna(col_median):
                    col_median = 0
                data_features[col] = data_features[col].fillna(col_median)
                # Replace infinite values
                data_features[col] = data_features[col].replace([np.inf, -np.inf], col_median)
            except Exception as e:
                # If there's an error with a column, fill with 0
                data_features[col] = data_features[col].fillna(0)
                data_features[col] = data_features[col].replace([np.inf, -np.inf], 0)
        
        # Apply feature selection based on importance
        important_features = self._get_important_features(sport_key, market_type)
        available_features = [col for col in important_features if col in data_features.columns]
        
        # Ensure we have all required features, fill missing with 0
        if available_features:
            # Only return the important features to match model expectations
            result_features = data_features[available_features].copy()
            
            # Add any missing features with 0 values
            for feat in important_features:
                if feat not in result_features.columns:
                    result_features[feat] = 0.0
            
            return result_features
        
        return data_features


    def _get_important_features(self, sport_key: str, market_type: str) -> List[str]:
        """
        Get list of important features for each sport/market combination
        LIMITED TO 7 CORE FEATURES to match trained ML models
        """
        # Core 7 features that all models were trained with
        # These are the only features the models expect
        core_features = [
            'home_win_pct',      # 1. Home team win percentage
            'away_win_pct',      # 2. Away team win percentage  
            'home_recent_form',  # 3. Home team recent form (last 5 games)
            'away_recent_form',  # 4. Away team recent form (last 5 games)
            'home_sos',          # 5. Home team strength of schedule
            'away_sos',          # 6. Away team strength of schedule
            'rest_days_diff'     # 7. Difference in rest days between teams
        ]
        
        # Return only the 7 core features - models were trained with exactly these
        return core_features
    
    def prepare_training_data(self, games_data: List[Dict], sport_key: str, market_type: str) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Prepare training data from ESPN historical games
        """
        if not games_data:
            raise ValueError(f"No games data provided for {sport_key} - {market_type}")
        
        # Convert list of game dicts to DataFrame
        df = pd.DataFrame(games_data)
        
        # Ensure required columns exist
        required_cols = ['home_score', 'away_score']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Prepare features using the standard pipeline
        X, y = self.prepare_features(df, sport_key, market_type)
        
        return X, y

    def _add_placeholder_features(self, df: pd.DataFrame, sport_key: str) -> pd.DataFrame:
        """
        Add placeholder features for single game prediction when historical data isn't available
        """
        # Comprehensive list of all features that might be expected by feature creation methods
        
        # Basic record features
        basic_features = [
            'home_wins', 'home_losses', 'away_wins', 'away_losses',
            'home_recent_wins', 'away_recent_wins', 'home_previous_wins', 'away_previous_wins',
            'home_home_wins', 'home_home_losses', 'home_away_wins', 'home_away_losses',
            'away_home_wins', 'away_home_losses', 'away_away_wins', 'away_away_losses',
            'home_points_for', 'home_points_against', 'away_points_for', 'away_points_against',
            'home_points_mean', 'away_points_mean', 'home_points_std', 'away_points_std',
            'home_season_form', 'away_season_form'
        ]
        
        # Historical H2H features
        h2h_features = [
            'historical_h2h_home_wins', 'historical_h2h_away_wins', 'recent_h2h_wins_home',
            'season_series_home_wins', 'season_series_away_wins'
        ]
        
        # vs top teams features
        top_team_features = [
            'home_vs_top_teams_wins', 'home_vs_top_teams_losses',
            'away_vs_top_teams_wins', 'away_vs_top_teams_losses'
        ]
        
        # Close games features
        close_game_features = [
            'home_close_games_wins', 'home_close_games_losses',
            'away_close_games_wins', 'away_close_games_losses'
        ]
        
        # ATS features
        ats_features = [
            'home_ats_wins', 'home_ats_losses', 'away_ats_wins', 'away_ats_losses',
            'home_avg_margin_vs_spread', 'away_avg_margin_vs_spread',
            'home_recent_ats_wins', 'away_recent_ats_wins'
        ]
        
        # Over/Under features
        ou_features = [
            'home_over_wins', 'home_under_wins', 'away_over_wins', 'away_under_wins'
        ]
        
        # Rest and schedule features
        rest_features = [
            'home_rest_days', 'away_rest_days',
            'home_time_zones_traveled', 'away_time_zones_traveled'
        ]
        
        # Opponent strength features
        opponent_features = [
            'home_opponent_win_pct', 'away_opponent_win_pct'
        ]
        
        # Travel features
        travel_features = [
            'home_travel_miles', 'away_travel_miles'
        ]
        
        # Date features
        date_features = [
            'game_date', 'home_last_game_date', 'away_last_game_date'
        ]
        
        # Injury features
        injury_features = [
            'home_injured_players', 'away_injured_players',
            'home_star_players_injured', 'away_star_players_injured',
            'home_injury_performance_impact', 'away_injury_performance_impact',
            # Basketball position-specific injuries
            'home_point_guard_injured', 'home_center_injured',
            'away_point_guard_injured', 'away_center_injured',
            # NFL position-specific injuries
            'home_quarterback_injured', 'home_running_back_injured', 'home_wide_receiver_injured',
            'away_quarterback_injured', 'away_running_back_injured', 'away_wide_receiver_injured',
            # MLB pitcher injuries
            'home_ace_pitcher_injured', 'home_closer_injured',
            'away_ace_pitcher_injured', 'away_closer_injured'
        ]
        
        # Weather features
        weather_features = [
            'temperature', 'wind_speed', 'precipitation', 'wind_direction'
        ]
        
        # Soccer-specific features
        soccer_features = [
            'home_goals_for', 'home_goals_against', 'away_goals_for', 'away_goals_against',
            'home_matches_played', 'away_matches_played',
            'home_expected_goals', 'away_expected_goals',
            'home_shots', 'away_shots',
            'home_possession_pct', 'away_possession_pct',
            'home_pass_completion_pct', 'away_pass_completion_pct',
            'home_yellow_cards', 'away_yellow_cards',
            'home_clean_sheets', 'away_clean_sheets'
        ]
        
        # Baseball-specific features
        baseball_features = [
            'home_runs_scored', 'home_runs_allowed', 'away_runs_scored', 'away_runs_allowed',
            'home_hits', 'away_hits', 'home_walks', 'away_walks',
            'home_hit_by_pitch', 'away_hit_by_pitch',
            'home_at_bats', 'away_at_bats',
            'home_sacrifice_flies', 'away_sacrifice_flies',
            'home_singles', 'away_singles', 'home_doubles', 'away_doubles',
            'home_triples', 'away_triples', 'home_home_runs', 'away_home_runs',
            'home_earned_runs', 'away_earned_runs', 'home_innings_pitched', 'away_innings_pitched',
            'home_strikeouts', 'away_strikeouts',
            'home_putouts', 'away_putouts', 'home_assists', 'away_assists', 'home_errors', 'away_errors'
        ]
        
        # NFL-specific features
        nfl_features = [
            'home_total_yards', 'away_total_yards',
            'home_plays', 'away_plays',
            'home_drives', 'away_drives',
            'home_passing_yards', 'away_passing_yards',
            'home_sack_yards', 'away_sack_yards',
            'home_pass_attempts', 'away_pass_attempts',
            'home_sacks', 'away_sacks',
            'home_interceptions', 'away_interceptions',
            'home_rushing_yards', 'away_rushing_yards',
            'home_rush_attempts', 'away_rush_attempts',
            'home_turnovers', 'away_turnovers',
            'home_third_down_conversions', 'away_third_down_conversions',
            'home_third_down_attempts', 'away_third_down_attempts',
            'home_red_zone_touchdowns', 'away_red_zone_touchdowns',
            'home_red_zone_attempts', 'away_red_zone_attempts'
        ]
        
        # NHL-specific features
        nhl_features = [
            'home_time_on_ice', 'away_time_on_ice',
            'home_shots_on_goal', 'away_shots_on_goal',
            'home_shots_against', 'away_shots_against',
            'home_missed_shots', 'away_missed_shots',
            'home_missed_shots_against', 'away_missed_shots_against',
            'home_blocked_shots', 'away_blocked_shots',
            'home_blocked_shots_against', 'away_blocked_shots_against',
            'home_power_play_goals', 'away_power_play_goals',
            'home_power_play_opportunities', 'away_power_play_opportunities',
            'home_power_play_goals_against', 'away_power_play_goals_against',
            'home_penalty_kill_opportunities', 'away_penalty_kill_opportunities'
        ]
        
        # Market line features
        market_features = [
            'spread_line', 'total_line', 'home_score', 'away_score'
        ]
        
        # Combine all feature lists
        all_features = (
            basic_features + h2h_features + top_team_features + close_game_features +
            ats_features + ou_features + rest_features + opponent_features +
            travel_features + date_features + injury_features + weather_features +
            soccer_features + baseball_features + nfl_features + nhl_features + market_features
        )
        
        # Build a dictionary of missing features to add all at once (prevents fragmentation)
        missing_features = {}
        for feature in all_features:
            if feature not in df.columns:
                if feature in ['game_date', 'home_last_game_date', 'away_last_game_date']:
                    missing_features[feature] = 0  # Use numeric 0 instead of Timestamp
                elif feature in ['home_opponent_win_pct', 'away_opponent_win_pct']:
                    missing_features[feature] = 0.5  # Average win percentage
                elif feature in ['home_season_form', 'away_season_form']:
                    missing_features[feature] = 0.5  # Average form
                elif feature in ['temperature']:
                    missing_features[feature] = 72  # Room temperature
                elif feature in ['wind_speed']:
                    missing_features[feature] = 5  # Light wind
                elif feature in ['precipitation']:
                    missing_features[feature] = 0  # No precipitation
                elif feature in ['wind_direction']:
                    missing_features[feature] = 0  # North
                else:
                    missing_features[feature] = 0
        
        # Add all missing features at once using pd.concat to prevent fragmentation
        if missing_features:
            # Ensure all values are properly sized lists to match df.index length
            n_rows = len(df.index)
            new_cols_df = pd.DataFrame({k: [v] * n_rows for k, v in missing_features.items()}, index=df.index)
            df = pd.concat([df, new_cols_df], axis=1)
        
        # Return a defragmented copy
        return df.copy()
