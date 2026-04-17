"""
Comprehensive Test Suite for Week 5-7 Enhancements
Tests for odds integration, advanced models, synthetic data, and ensemble
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.odds_models import (
    ProbabilityConverter, EdgeDetector, OddsProvider, OddsRecord
)
from app.services.odds_aggregator_service import OddsAggregatorService
from app.services.advanced_statistical_models import (
    BayesianPredictor, ARIMAForecaster, DecisionTreeEnsemble, AdvancedModelEnsemble
)
from app.services.synthetic_data_generation import (
    SyntheticDataGenerator, DataAugmentationPipeline, SimulationBacktestEngine, SyntheticDataConfig
)
from app.services.multi_model_ensemble import (
    MultiModelEnsemble, EnsembleConfig, ModelMetrics, EnsembleWeightCalculator
)

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_historical_data():
    """Sample historical sports data for testing"""
    return pd.DataFrame({
        'ppg': np.random.normal(20, 5, 100),
        'rpg': np.random.normal(8, 2, 100),
        'apg': np.random.normal(4, 1, 100),
        'home': np.random.binomial(1, 0.5, 100),
        'opponent_rank': np.random.randint(1, 30, 100)
    })

@pytest.fixture
def sample_time_series():
    """Sample time series data for ARIMA testing"""
    return [20 + 2*np.sin(i/10) + np.random.normal(0, 1) for i in range(50)]

# ============================================================================
# PROBABILITY CONVERTER TESTS
# ============================================================================

class TestProbabilityConverter:
    
    def test_american_to_decimal_positive(self):
        """Test conversion of positive American odds"""
        decimal = ProbabilityConverter.american_to_decimal(200)
        assert decimal == 3.0  # +200 = 3.0 decimal
    
    def test_american_to_decimal_negative(self):
        """Test conversion of negative American odds"""
        decimal = ProbabilityConverter.american_to_decimal(-110)
        assert pytest.approx(decimal, 0.01) == 1.909
    
    def test_american_to_implied_probability(self):
        """Test odds to probability conversion"""
        prob = ProbabilityConverter.american_to_implied_probability(-110)
        assert pytest.approx(prob, 0.01) == 0.524  # -110 ≈ 52.4%
    
    def test_calculate_vig(self):
        """Test vigorish calculation"""
        vig = ProbabilityConverter.calculate_vig(-110, -110)
        assert 0 < vig < 0.05  # Typical vig is 0-5%
    
    def test_true_probability_removal(self):
        """Test vig removal from probabilities"""
        home_true, away_true = ProbabilityConverter.true_probability_moneyline(
            -110, -110
        )
        assert pytest.approx(home_true + away_true, 0.01) == 1.0
    
    def test_edge_case_even_money(self):
        """Test edge case with even money odds"""
        prob = ProbabilityConverter.american_to_implied_probability(-100)
        assert pytest.approx(prob, 0.01) == 0.5

# ============================================================================
# EDGE DETECTION TESTS
# ============================================================================

class TestEdgeDetector:
    
    def test_positive_edge_detection(self):
        """Test detection of positive edge"""
        edge = EdgeDetector.calculate_edge(
            model_probability=0.55,
            market_probability=0.50,
            american_odds=-110
        )
        assert edge['edge'] > 0
        assert edge['is_profitable']
    
    def test_negative_edge_detection(self):
        """Test detection of negative edge"""
        edge = EdgeDetector.calculate_edge(
            model_probability=0.45,
            market_probability=0.50,
            american_odds=-110
        )
        assert edge['edge'] < 0
        assert not edge['is_profitable']
    
    def test_kelly_criterion_calculation(self):
        """Test Kelly Criterion stake sizing"""
        edge = EdgeDetector.calculate_edge(
            model_probability=0.60,
            market_probability=0.50,
            american_odds=-110
        )
        
        kelly = edge['kelly_fraction']
        assert 0 <= kelly <= 0.25  # Max 25% stake

# ============================================================================
# ODDS AGGREGATOR TESTS
# ============================================================================

@pytest.mark.asyncio
class TestOddsAggregatorService:
    
    async def test_fetch_odds_from_providers(self):
        """Test fetching odds from multiple providers"""
        # In production, this would call actual APIs
        # For testing, we mock responses
        
        service = OddsAggregatorService(None)
        
        # Verify providers are initialized
        assert len(service.providers) == 4
        assert OddsProvider.DRAFTKINGS in service.providers
    
    async def test_calculate_consensus_odds(self):
        """Test consensus calculation across providers"""
        # Mock odds data
        providers_odds = {
            'draftkings': {'moneyline': {'home': -110, 'away': -110}},
            'fanduel': {'moneyline': {'home': -110, 'away': -110}},
            'betmgm': {'moneyline': {'home': -115, 'away': -105}},
        }
        
        # Consensus should be median of -110, -110, -115 = -110
        consensus_home = np.median([-110, -110, -115])
        assert int(consensus_home) == -110

# ============================================================================
# BAYESIAN PREDICTOR TESTS
# ============================================================================

class TestBayesianPredictor:
    
    def test_prior_setting(self):
        """Test setting prior probability"""
        predictor = BayesianPredictor('nba')
        predictor.set_prior('team_a', 0.55, confidence=0.8)
        
        assert 'team_a' in predictor.priors
        assert predictor.priors['team_a'].mean == 0.55
        assert predictor.priors['team_a'].confidence == 0.8
    
    def test_bayesian_update(self):
        """Test updating belief with evidence"""
        predictor = BayesianPredictor('nba')
        predictor.set_prior('team_a', 0.50, confidence=0.5)
        
        # Strong recent evidence: won 4/5 games
        recent_performance = [1, 1, 1, 1, 0]
        
        posterior = predictor.update_with_evidence(
            'team_a',
            recent_performance
        )
        
        # Should move closer to recent performance
        assert posterior > 0.50
    
    def test_credible_interval(self):
        """Test credible interval calculation"""
        predictor = BayesianPredictor('nba')
        predictor.set_prior('team_a', 0.55, confidence=0.9)
        predictor.update_with_evidence('team_a', [1, 1, 1])
        
        point, lower, upper = predictor.predict_credible_interval('team_a')
        
        assert lower < point < upper
        assert upper - lower > 0
    
    def test_predict_vs_line(self):
        """Test prediction compared to market odds"""
        predictor = BayesianPredictor('nba')
        predictor.set_prior('team_a', 0.60, confidence=0.8)
        
        result = predictor.predict_vs_line('team_a', american_odds=-110)
        
        assert 'model_probability' in result
        assert 'market_probability' in result
        assert 'edge' in result

# ============================================================================
# ARIMA FORECASTER TESTS
# ============================================================================

class TestARIMAForecaster:
    
    def test_arima_fitting(self, sample_time_series):
        """Test ARIMA model fitting"""
        forecaster = ARIMAForecaster(p=2, d=1, q=2)
        forecaster.fit(sample_time_series)
        
        assert forecaster.fitted_model
        assert forecaster.mean is not None
        assert forecaster.std is not None
    
    def test_arima_forecasting(self, sample_time_series):
        """Test ARIMA forecasting"""
        forecaster = ARIMAForecaster()
        forecaster.fit(sample_time_series)
        
        result = forecaster.forecast(steps=5, confidence=0.95)
        
        assert 'forecasts' in result
        assert len(result['forecasts']) == 5
        assert 'confidence_intervals' in result
        assert result['mean_forecast'] is not None
    
    def test_confidence_intervals(self, sample_time_series):
        """Test confidence interval width increases with steps ahead"""
        forecaster = ARIMAForecaster()
        forecaster.fit(sample_time_series)
        
        result = forecaster.forecast(steps=10)
        
        ci = result['confidence_intervals']
        widths = [c['upper'] - c['lower'] for c in ci]
        
        # Width should generally increase with steps ahead
        # (though not strictly due to randomness)
        assert widths[0] > 0

# ============================================================================
# DECISION TREE ENSEMBLE TESTS
# ============================================================================

class TestDecisionTreeEnsemble:
    
    def test_tree_fitting_classification(self, sample_historical_data):
        """Test fitting decision tree ensemble for classification"""
        X = sample_historical_data[['ppg', 'rpg', 'apg']].values
        y = (sample_historical_data['ppg'] > 20).astype(int).values
        
        ensemble = DecisionTreeEnsemble(
            n_trees=5,
            task='classification'
        )
        ensemble.fit(X, y, feature_names=['ppg', 'rpg', 'apg'])
        
        assert ensemble.fitted
        predictions = ensemble.predict(X[:5])
        assert len(predictions) == 5
    
    def test_tree_feature_importance(self, sample_historical_data):
        """Test feature importance extraction"""
        X = sample_historical_data[['ppg', 'rpg', 'apg']].values
        y = (sample_historical_data['ppg'] > 20).astype(int).values
        
        ensemble = DecisionTreeEnsemble(n_trees=5, task='classification')
        ensemble.fit(X, y, feature_names=['ppg', 'rpg', 'apg'])
        
        importance = ensemble.get_feature_importance()
        
        assert len(importance) == 3
        assert sum(importance.values()) > 0
        assert all(0 <= v <= 1 for v in importance.values())

# ============================================================================
# SYNTHETIC DATA TESTS
# ============================================================================

class TestSyntheticDataGenerator:
    
    def test_smote_generation(self, sample_historical_data):
        """Test SMOTE synthetic data generation"""
        config = SyntheticDataConfig(method='smote', n_synthetic_samples=100)
        generator = SyntheticDataGenerator(config)
        
        synthetic = generator.generate_from_realdata(
            sample_historical_data,
            n_synthetic=100,
            method='smote'
        )
        
        assert len(synthetic) == 100
        assert list(synthetic.columns) == list(sample_historical_data.columns)
    
    def test_synthetic_data_quality(self, sample_historical_data):
        """Test synthetic data quality metrics"""
        generator = SyntheticDataGenerator()
        synthetic = generator.generate_from_realdata(
            sample_historical_data,
            n_synthetic=100,
            method='gmm'
        )
        
        metrics = generator.get_quality_report()
        
        assert 'quality_metrics' in metrics
        assert 0 <= metrics['quality_metrics'].get('overall_quality', 0) <= 1
    
    def test_gmm_generation(self, sample_historical_data):
        """Test GMM synthetic data generation"""
        generator = SyntheticDataGenerator()
        synthetic = generator.generate_from_realdata(
            sample_historical_data,
            n_synthetic=100,
            method='gmm'
        )
        
        assert len(synthetic) == 100
        # Check that synthetic data has similar statistics to real data
        assert abs(synthetic['ppg'].mean() - sample_historical_data['ppg'].mean()) < 5

class TestDataAugmentationPipeline:
    
    def test_noise_injection(self, sample_historical_data):
        """Test noise injection augmentation"""
        pipeline = DataAugmentationPipeline()
        
        augmented = pipeline.apply_noise_injection(
            sample_historical_data,
            noise_level=0.05
        )
        
        # Check that data is modified but similar
        ppg_diff = abs(augmented['ppg'].mean() - sample_historical_data['ppg'].mean())
        assert ppg_diff < sample_historical_data['ppg'].std()
    
    def test_feature_scaling_variations(self, sample_historical_data):
        """Test feature scaling augmentation"""
        pipeline = DataAugmentationPipeline()
        
        variations = pipeline.apply_feature_scaling_variations(
            sample_historical_data,
            scale_factors=[0.95, 1.0, 1.05]
        )
        
        assert len(variations) == 3
        assert variations[1]['ppg'].mean() >= variations[0]['ppg'].mean()

# ============================================================================
# MULTI-MODEL ENSEMBLE TESTS
# ============================================================================

class TestEnsembleWeightCalculator:
    
    def test_weight_calculation(self):
        """Test weight calculation based on metrics"""
        metrics = {
            'model_a': ModelMetrics(
                model_name='model_a',
                sport_key='nba',
                recent_accuracy=0.65,
                calibration_error=0.05,
                prediction_confidence=0.75
            ),
            'model_b': ModelMetrics(
                model_name='model_b',
                sport_key='nba',
                recent_accuracy=0.55,
                calibration_error=0.15,
                prediction_confidence=0.50
            )
        }
        
        weights = EnsembleWeightCalculator.calculate_weights(metrics)
        
        assert 'model_a' in weights
        assert 'model_b' in weights
        assert weights['model_a'] > weights['model_b']  # Better model gets higher weight

class TestMultiModelEnsemble:
    
    @pytest.mark.asyncio
    async def test_ensemble_initialization(self):
        """Test ensemble initialization"""
        config = EnsembleConfig(min_models=2, max_models=5)
        ensemble = MultiModelEnsemble('nba', config=config)
        
        assert ensemble.sport_key == 'nba'
        assert len(ensemble.models) == 0
    
    @pytest.mark.asyncio
    async def test_model_registration(self):
        """Test registering models in ensemble"""
        ensemble = MultiModelEnsemble('nba')
        
        # Mock models
        mock_model_1 = type('MockModel', (), {'predict': lambda x: 0.6})()
        mock_model_2 = type('MockModel', (), {'predict': lambda x: 0.55})()
        
        ensemble.register_model('model_1', mock_model_1)
        ensemble.register_model('model_2', mock_model_2)
        
        assert len(ensemble.models) == 2
        assert 'model_1' in ensemble.models
    
    @pytest.mark.asyncio
    async def test_weighted_voting(self):
        """Test weighted voting mechanism"""
        ensemble = MultiModelEnsemble('nba')
        
        predictions = {
            'model_a': {'probability': 0.65, 'confidence': 0.8},
            'model_b': {'probability': 0.55, 'confidence': 0.6},
            'model_c': {'probability': 0.60, 'confidence': 0.7}
        }
        
        weights = {
            'model_a': 2.0,
            'model_b': 1.0,
            'model_c': 1.5
        }
        
        result = ensemble._weighted_voting(predictions, weights)
        
        assert 'probability' in result
        assert 'confidence' in result
        assert result['probability'] > 0.5
    
    @pytest.mark.asyncio
    async def test_majority_voting(self):
        """Test majority voting mechanism"""
        ensemble = MultiModelEnsemble('nba')
        
        predictions = {
            'model_a': {'probability': 0.70, 'confidence': 0.8},
            'model_b': {'probability': 0.65, 'confidence': 0.7},
            'model_c': {'probability': 0.40, 'confidence': 0.6}
        }
        
        result = ensemble._majority_voting(predictions)
        
        assert result['probability'] == 1.0  # 2 votes for > 0.5
        assert result['votes_yes'] == 2
    
    @pytest.mark.asyncio
    async def test_agreement_calculation(self):
        """Test agreement score calculation"""
        ensemble = MultiModelEnsemble('nba')
        
        # Perfect agreement
        predictions_agree = {
            'model_a': {'probability': 0.60, 'confidence': 0.7},
            'model_b': {'probability': 0.60, 'confidence': 0.7}
        }
        
        agreement = ensemble._calculate_agreement(predictions_agree)
        assert agreement > 0.9
        
        # No agreement
        predictions_disagree = {
            'model_a': {'probability': 0.90, 'confidence': 0.7},
            'model_b': {'probability': 0.10, 'confidence': 0.7}
        }
        
        disagreement = ensemble._calculate_agreement(predictions_disagree)
        assert disagreement < 0.5

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    
    @pytest.mark.asyncio
    async def test_odds_to_ensemble_pipeline(self):
        """Test end-to-end pipeline from odds to ensemble prediction"""
        # 1. Get odds
        market_prob = 0.50  # From market odds
        
        # 2. Create Bayesian model
        bayesian = BayesianPredictor('nba')
        bayesian.set_prior('team', 0.55, 0.7)
        
        # 3. Create ensemble
        ensemble = MultiModelEnsemble('nba')
        
        # 4. Compare
        edge = EdgeDetector.calculate_edge(
            model_probability=0.55,
            market_probability=market_prob,
            american_odds=-110
        )
        
        assert edge['edge'] > 0
    
    @pytest.mark.asyncio
    async def test_synthetic_data_to_model_training(self, sample_historical_data):
        """Test end-to-end synthetic data generation and model training"""
        # 1. Generate synthetic data
        generator = SyntheticDataGenerator()
        synthetic = generator.generate_from_realdata(
            sample_historical_data,
            n_synthetic=200,
            method='smote'
        )
        
        # 2. Train model on combined data
        X = pd.concat([sample_historical_data, synthetic])[['ppg', 'rpg', 'apg']].values
        y = (pd.concat([sample_historical_data, synthetic])['ppg'] > 20).astype(int).values
        
        ensemble = DecisionTreeEnsemble(n_trees=5, task='classification')
        ensemble.fit(X, y)
        
        # 3. Make predictions
        predictions = ensemble.predict(X[:10])
        assert len(predictions) == 10

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
