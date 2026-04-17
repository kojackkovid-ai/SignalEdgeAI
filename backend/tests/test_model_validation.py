import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch
from app.services.model_validation import ModelValidator

@pytest.fixture
def validator():
    return ModelValidator()

@pytest.fixture
def sample_predictions():
    return pd.DataFrame({
        'predicted_probability': np.random.rand(100),
        'actual_outcome': np.random.randint(0, 2, 100),
        'predicted_winner': np.random.randint(0, 2, 100),
        'game_date': pd.date_range('2024-01-01', periods=100, freq='D'),
        'sport_key': ['basketball_nba'] * 100
    })

@pytest.fixture
def sample_betting_data():
    return pd.DataFrame({
        'predicted_probability': np.random.rand(50),
        'actual_outcome': np.random.randint(0, 2, 50),
        'odds': np.random.choice([-110, 100, -150, 130], 50),
        'stake': np.ones(50) * 100,  # $100 bets
        'game_date': pd.date_range('2024-01-01', periods=50, freq='D')
    })

def test_calculate_accuracy(validator, sample_predictions):
    accuracy = validator._calculate_accuracy(sample_predictions)
    
    assert 0 <= accuracy <= 1
    assert isinstance(accuracy, float)

def test_calculate_precision_recall_f1(validator, sample_predictions):
    metrics = validator._calculate_precision_recall_f1(sample_predictions)
    
    assert 'precision' in metrics
    assert 'recall' in metrics
    assert 'f1_score' in metrics
    assert 0 <= metrics['precision'] <= 1
    assert 0 <= metrics['recall'] <= 1
    assert 0 <= metrics['f1_score'] <= 1

def test_calculate_auc_roc(validator, sample_predictions):
    auc_roc = validator._calculate_auc_roc(sample_predictions)
    
    assert 0 <= auc_roc <= 1
    assert isinstance(auc_roc, float)

def test_calculate_log_loss(validator, sample_predictions):
    log_loss = validator._calculate_log_loss(sample_predictions)
    
    assert log_loss >= 0
    assert isinstance(log_loss, float)

def test_calculate_brier_score(validator, sample_predictions):
    brier_score = validator._calculate_brier_score(sample_predictions)
    
    assert 0 <= brier_score <= 1
    assert isinstance(brier_score, float)

def test_calculate_calibration(validator, sample_predictions):
    calibration = validator._calculate_calibration(sample_predictions)
    
    assert 'calibration_curve' in calibration
    assert 'reliability_diagram' in calibration
    assert 'calibration_error' in calibration
    assert calibration['calibration_error'] >= 0

def test_calculate_betting_metrics(validator, sample_betting_data):
    betting_metrics = validator._calculate_betting_metrics(sample_betting_data)
    
    assert 'total_return' in betting_metrics
    assert 'roi_percentage' in betting_metrics
    assert 'win_rate' in betting_metrics
    assert 'average_odds' in betting_metrics
    assert 'longest_win_streak' in betting_metrics
    assert 'longest_lose_streak' in betting_metrics
    assert isinstance(betting_metrics['roi_percentage'], float)

def test_calculate_sharpe_ratio(validator, sample_betting_data):
    sharpe_ratio = validator._calculate_sharpe_ratio(sample_betting_data)
    
    assert isinstance(sharpe_ratio, float)

def test_calculate_max_drawdown(validator, sample_betting_data):
    max_drawdown = validator._calculate_max_drawdown(sample_betting_data)
    
    assert 0 <= max_drawdown <= 1
    assert isinstance(max_drawdown, float)

def test_time_series_cross_validation(validator):
    # Mock prediction function
    def mock_predict_func(X):
        return np.random.rand(len(X))
    
    # Create time series data
    X = pd.DataFrame({'feature1': np.random.rand(100), 'feature2': np.random.rand(100)})
    y = np.random.randint(0, 2, 100)
    
    cv_scores = validator.time_series_cross_validation(mock_predict_func, X, y, n_splits=5)
    
    assert len(cv_scores) == 5
    assert all(0 <= score <= 1 for score in cv_scores)

def test_monte_carlo_validation(validator, sample_predictions):
    mc_results = validator.monte_carlo_validation(sample_predictions, n_simulations=100)
    
    assert 'accuracy_distribution' in mc_results
    assert 'confidence_intervals' in mc_results
    assert 'p_value' in mc_results
    assert len(mc_results['accuracy_distribution']) == 100

def test_statistical_significance_test(validator, sample_predictions):
    significance = validator.statistical_significance_test(sample_predictions)
    
    assert 'chi2_statistic' in significance
    assert 'p_value' in significance
    assert 'is_significant' in significance
    assert 0 <= significance['p_value'] <= 1

def test_validate_model_performance(validator, sample_predictions, sample_betting_data):
    # Combine predictions and betting data
    combined_data = sample_predictions.copy()
    combined_data['odds'] = np.random.choice([-110, 100, -150, 130], len(combined_data))
    combined_data['stake'] = np.ones(len(combined_data)) * 100
    
    results = validator.validate_model_performance(combined_data)
    
    assert 'accuracy' in results
    assert 'precision_recall_f1' in results
    assert 'auc_roc' in results
    assert 'log_loss' in results
    assert 'brier_score' in results
    assert 'calibration' in results
    assert 'betting_metrics' in results
    assert 'sharpe_ratio' in results
    assert 'max_drawdown' in results

def test_generate_validation_report(validator, sample_predictions, sample_betting_data):
    # Combine predictions and betting data
    combined_data = sample_predictions.copy()
    combined_data['odds'] = np.random.choice([-110, 100, -150, 130], len(combined_data))
    combined_data['stake'] = np.ones(len(combined_data)) * 100
    
    report = validator.generate_validation_report(combined_data)
    
    assert 'performance_summary' in report
    assert 'detailed_metrics' in report
    assert 'betting_analysis' in report
    assert 'recommendations' in report
    assert 'risk_assessment' in report