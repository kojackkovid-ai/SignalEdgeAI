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
        Prepare features for a single game prediction
        """
        try:
            # Convert single game data to DataFrame format
            df = pd.DataFrame([game_data])
            
            # Add placeholder columns for features that would come from historical data
            df = self._add_placeholder_features(df, sport_key)
            
            # Prepare features using the same pipeline
            X, _ = self.prepare_features(df, sport_key, market_type)
            
            # AGGRESSIVE 3D TO 2D CONVERSION
            # Get the raw values and force reshape to 2D
            raw_values = X.values if isinstance(X, pd.DataFrame) else np.array(X)
            
            logger.debug(f"Raw values shape: {raw_values.shape}, ndim: {raw_values.ndim}")
            
            # Flatten completely and reshape to (1, n_features)
            flat_values = np.asarray(raw_values).ravel()
            n_features = len(flat_values)
            
            # Create properly shaped 2D array
            X_2d = flat_values.reshape(1, n_features)
            
            logger.debug(f"Final 2D shape: {X_2d.shape}")
            
            # Get column names if available
            if isinstance(X, pd.DataFrame) and len(X.columns) == n_features:
                return pd.DataFrame(X_2d, columns=X.columns)
            else:
                return pd.DataFrame(X_2d)
            
        except Exception as e:
            logger.error(f"Error preparing single game features: {e}")
            raise

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
        
