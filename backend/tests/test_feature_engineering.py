import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch
from app.services.data_preprocessing import AdvancedFeatureEngineer

@pytest.fixture
def feature_engineer():
    return AdvancedFeatureEngineer()

@pytest.fixture
def sample_game_data():
    # Create sample game data for NBA
    return pd.DataFrame({
        'home_team': ['Lakers', 'Warriors', 'Celtics'] * 10,
        'away_team': ['Celtics', 'Lakers', 'Warriors'] * 10,
        'home_score': np.random.randint(90, 120, 30),
        'away_score': np.random.randint(90, 120, 30),
        'home_fg_pct': np.random.rand(30) * 0.5 + 0.3,
        'away_fg_pct': np.random.rand(30) * 0.5 + 0.3,
        'home_rebounds': np.random.randint(35, 55, 30),
        'away_rebounds': np.random.randint(35, 55, 30),
        'home_turnovers': np.random.randint(8, 20, 30),
        'away_turnovers': np.random.randint(8, 20, 30),
        'game_date': pd.date_range('2024-01-01', periods=30, freq='D')
    })

def test_prepare_features_nba(feature_engineer, sample_game_data):
    features, labels = feature_engineer.prepare_features(sample_game_data, 'basketball_nba', 'moneyline')
    
    assert isinstance(features, pd.DataFrame)
    assert isinstance(labels, np.ndarray)
    assert len(features) == len(labels)
    assert features.shape[1] > sample_game_data.shape[1]  # Should have more features after engineering

def test_create_sport_specific_features_nba(feature_engineer, sample_game_data):
    result = feature_engineer._create_sport_specific_features(sample_game_data, 'basketball_nba')
    
    # Check for NBA-specific features
    expected_features = [
        'pace', 'home_offensive_rating', 'away_offensive_rating',
        'home_defensive_rating', 'away_defensive_rating'
    ]
    
    for feature in expected_features:
        assert feature in result.columns

def test_create_sport_specific_features_nfl(feature_engineer):
    nfl_data = pd.DataFrame({
        'home_team': ['Patriots', 'Cowboys', 'Packers'] * 10,
        'away_team': ['Packers', 'Patriots', 'Cowboys'] * 10,
        'home_score': np.random.randint(14, 35, 30),
        'away_score': np.random.randint(14, 35, 30),
        'home_passing_yards': np.random.randint(150, 400, 30),
        'away_passing_yards': np.random.randint(150, 400, 30),
        'home_rushing_yards': np.random.randint(50, 200, 30),
        'away_rushing_yards': np.random.randint(50, 200, 30),
        'home_turnovers': np.random.randint(0, 4, 30),
        'away_turnovers': np.random.randint(0, 4, 30),
        'game_date': pd.date_range('2024-01-01', periods=30, freq='D')
    })
    
    result = feature_engineer._create_sport_specific_features(nfl_data, 'americanfootball_nfl')
    
    # Check for NFL-specific features
    expected_features = [
        'home_passing_efficiency', 'away_passing_efficiency',
        'home_rushing_efficiency', 'away_rushing_efficiency'
    ]
    
    for feature in expected_features:
        assert feature in result.columns

def test_create_rolling_features(feature_engineer, sample_game_data):
    result = feature_engineer._create_rolling_features(sample_game_data, ['home_score', 'away_score'])
    
    # Check for rolling features
    expected_features = [
        'home_score_rolling_mean_3', 'home_score_rolling_mean_5',
        'away_score_rolling_mean_3', 'away_score_rolling_mean_5'
    ]
    
    for feature in expected_features:
        assert feature in result.columns

def test_create_elo_ratings(feature_engineer, sample_game_data):
    result = feature_engineer._create_elo_ratings(sample_game_data)
    
    # Check for ELO features
    expected_features = [
        'home_elo', 'away_elo', 'elo_difference'
    ]
    
    for feature in expected_features:
        assert feature in result.columns

def test_handle_missing_values(feature_engineer, sample_game_data):
    # Introduce missing values
    sample_game_data.loc[5:10, 'home_score'] = np.nan
    
    result = feature_engineer._handle_missing_values(sample_game_data)
    
    # Should not have any missing values
    assert not result.isnull().any().any()

def test_normalize_features(feature_engineer, sample_game_data):
    result = feature_engineer._normalize_features(sample_game_data)
    
    # Check that numeric features are normalized
    numeric_cols = result.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        if col in result.columns:
            # Values should be roughly between -3 and 3 (z-score normalized)
            assert result[col].mean() < 1.0
            assert result[col].std() < 2.0