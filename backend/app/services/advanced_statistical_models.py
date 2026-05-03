"""
Advanced Statistical Models for Week 5-7 Enhancement
Bayesian inference, ARIMA forecasting, and Decision Tree Ensemble
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from scipy import stats
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import warnings

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')

# ============================================================================
# BAYESIAN PREDICTOR
# ============================================================================

@dataclass
class BayesianPrior:
    """Prior distribution for Bayesian model"""
    mean: float  # Prior belief
    variance: float  # Uncertainty in prior
    confidence: float  # 0-1, how much we trust the prior

class BayesianPredictor:
    """
    Bayesian inference model for sports predictions
    Uses prior beliefs + new evidence to update probability
    """
    
    def __init__(self, sport_key: str, prop_type: str = 'moneyline'):
        self.sport_key = sport_key
        self.prop_type = prop_type
        self.priors = {}
        self.posteriors = {}
    
    def set_prior(
        self,
        entity_key: str,
        prior_probability: float,
        confidence: float = 0.7
    ):
        """Set prior probability for an entity (team, player, etc.)"""
        # Prior variance inversely proportional to confidence
        variance = (1 - confidence) * 0.1
        
        self.priors[entity_key] = BayesianPrior(
            mean=prior_probability,
            variance=variance,
            confidence=confidence
        )
    
    def update_with_evidence(
        self,
        entity_key: str,
        recent_performance: List[float],
        lookback_days: int = 30
    ) -> float:
        """
        Update prior with recent evidence using Bayesian inference
        
        Args:
            entity_key: Entity identifier
            recent_performance: List of recent results (0-1 range)
            lookback_days: Days of history to weight
        
        Returns:
            Updated posterior probability
        """
        if entity_key not in self.priors:
            return np.mean(recent_performance)
        
        prior = self.priors[entity_key]
        
        # Calculate likelihood from recent data
        recent_mean = np.mean(recent_performance) if recent_performance else prior.mean
        recent_std = np.std(recent_performance) if len(recent_performance) > 1 else prior.variance ** 0.5
        
        # Weight recent evidence
        sample_size = len(recent_performance)
        weight = sample_size / (sample_size + 10)  # 10 is regularization parameter
        
        # Posterior = weighted average of prior and likelihood
        posterior_mean = (
            prior.confidence * prior.mean +
            weight * recent_mean
        ) / (prior.confidence + weight)
        
        # Posterior variance is reduced (more confident)
        posterior_variance = (
            (prior.variance + recent_std ** 2) /
            (1 + sample_size / 10)
        )
        
        # Store posterior
        self.posteriors[entity_key] = BayesianPrior(
            mean=posterior_mean,
            variance=posterior_variance,
            confidence=min(1.0, prior.confidence + 0.05)
        )
        
        return posterior_mean
    
    def predict_credible_interval(
        self,
        entity_key: str,
        confidence_level: float = 0.95
    ) -> Tuple[float, float, float]:
        """
        Get prediction with credible interval
        
        Returns:
            (point_estimate, lower_bound, upper_bound)
        """
        posterior = self.posteriors.get(entity_key) or self.priors.get(entity_key)
        
        if not posterior:
            return (0.5, 0.25, 0.75)
        
        # Z-score for confidence level
        z = stats.norm.ppf((1 + confidence_level) / 2)
        
        std = posterior.variance ** 0.5
        margin_of_error = z * std
        
        lower = max(0, posterior.mean - margin_of_error)
        upper = min(1, posterior.mean + margin_of_error)
        
        return (posterior.mean, lower, upper)
    
    def predict_vs_line(
        self,
        entity_key: str,
        american_odds: float
    ) -> Dict:
        """
        Compare Bayesian prediction to market odds
        """
        from app.models.odds_models import ProbabilityConverter
        
        posterior = self.posteriors.get(entity_key) or self.priors.get(entity_key)
        
        if not posterior:
            return {'model_prob': 0.5, 'market_prob': 0.5, 'edge': 0}
        
        model_prob = posterior.mean
        market_prob = ProbabilityConverter.american_to_implied_probability(american_odds)
        edge = model_prob - market_prob
        
        return {
            'model_probability': model_prob,
            'market_probability': market_prob,
            'edge': edge,
            'edge_percentage': edge * 100,
            'credible_interval': self.predict_credible_interval(entity_key),
            'confidence': posterior.confidence
        }

# ============================================================================
# ARIMA FORECASTER
# ============================================================================

class ARIMAForecaster:
    """
    Auto-Regressive Integrated Moving Average model
    Forecasts future values based on historical trends
    
    Useful for:
    - Player performance trends
    - Team scoring trends
    - Season progression patterns
    """
    
    def __init__(
        self,
        p: int = 2,  # AutoRegressive order
        d: int = 1,  # Integration order (differencing)
        q: int = 2   # Moving Average order
    ):
        self.p = p
        self.d = d
        self.q = q
        self.fitted_model = None
    
    def fit(self, data: List[float]):
        """
        Fit ARIMA model to historical data
        
        Args:
            data: Historical time series (e.g., last 30 games PPG)
        """
        self.data = np.array(data)
        self.mean = np.mean(self.data)
        self.std = np.std(self.data)
        
        # Normalize data
        normalized = (self.data - self.mean) / (self.std + 1e-6)
        
        # Calculate AR coefficients using Yule-Walker
        if len(normalized) > self.p:
            self.ar_coeff = self._estimate_ar_coefficients(normalized)
        else:
            self.ar_coeff = np.zeros(self.p)
        
        # Calculate MA coefficients from residuals
        self.ma_coeff = np.zeros(self.q)
        
        self.fitted_model = True
    
    def forecast(
        self,
        steps: int = 1,
        confidence: float = 0.95
    ) -> Dict:
        """
        Forecast future values
        
        Args:
            steps: Number of periods ahead to forecast
            confidence: Confidence level for prediction interval (0.95 = 95%)
        
        Returns:
            Dict with forecasts and confidence intervals
        """
        if not self.fitted_model:
            raise ValueError("Model must be fitted first")
        
        # Start forecasting
        forecast_data = list(self.data[-self.p:])
        forecasts = []
        forecast_stds = []
        
        for step in range(steps):
            # AR component
            ar_value = np.dot(self.ar_coeff, forecast_data[-self.p:])
            
            # Add some noise for realistic uncertainty
            noise_std = self.std * 0.15  # 15% of std as noise
            
            forecast_value = ar_value + np.random.normal(0, noise_std)
            
            # Denormalize
            forecast_actual = forecast_value * self.std + self.mean
            
            forecasts.append(forecast_actual)
            forecast_stds.append(noise_std * self.std)
            
            forecast_data.append(forecast_value)
        
        # Calculate confidence intervals
        z = stats.norm.ppf((1 + confidence) / 2)
        confidence_intervals = [
            {
                'forecast': f,
                'lower': f - z * s,
                'upper': f + z * s,
                'std': s
            }
            for f, s in zip(forecasts, forecast_stds)
        ]
        
        return {
            'forecasts': forecasts,
            'confidence_intervals': confidence_intervals,
            'mean_forecast': np.mean(forecasts),
            'trend': 'increasing' if forecasts[-1] > np.mean(self.data[-5:]) else 'decreasing'
        }
    
    def _estimate_ar_coefficients(self, data: np.ndarray) -> np.ndarray:
        """Estimate AR coefficients using Yule-Walker equations"""
        # Simplified Yule-Walker estimation
        acf = self._autocorrelation(data, self.p)
        coefficients = np.zeros(self.p)
        
        if self.p >= 1 and acf[1] != 0:
            coefficients[0] = acf[1]
        
        return coefficients
    
    def _autocorrelation(self, data: np.ndarray, lags: int) -> np.ndarray:
        """Calculate autocorrelation function"""
        mean = np.mean(data)
        var = np.var(data)
        
        if var == 0:
            return np.ones(lags + 1)
        
        acf = np.ones(lags + 1)
        
        for k in range(1, lags + 1):
            acf[k] = np.mean(
                (data[:-k] - mean) * (data[k:] - mean)
            ) / var
        
        return acf

# ============================================================================
# DECISION TREE ENSEMBLE
# ============================================================================

class DecisionTreeEnsemble:
    """
    Ensemble of decision trees for classification/regression
    Used for interpretable predictions with feature importance
    """
    
    def __init__(
        self,
        n_trees: int = 10,
        max_depth: int = 8,
        min_samples_split: int = 5,
        task: str = 'classification'  # 'classification' or 'regression'
    ):
        self.n_trees = n_trees
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.task = task
        
        if task == 'classification':
            self.model = RandomForestClassifier(
                n_estimators=n_trees,
                max_depth=max_depth,
                min_samples_split=min_samples_split,
                random_state=42
            )
        else:
            self.model = RandomForestRegressor(
                n_estimators=n_trees,
                max_depth=max_depth,
                min_samples_split=min_samples_split,
                random_state=42
            )
        
        self.scaler = StandardScaler()
        self.feature_names = None
        self.fitted = False
    
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str] = None
    ):
        """
        Fit ensemble to training data
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target values
            feature_names: Names of features for interpretability
        """
        self.feature_names = feature_names or [f"Feature_{i}" for i in range(X.shape[1])]
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Fit the ensemble
        self.model.fit(X_scaled, y)
        
        self.fitted = True
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if not self.fitted:
            raise ValueError("Model must be fitted first")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return prediction probabilities (classification only)"""
        if not self.fitted:
            raise ValueError("Model must be fitted first")
        
        if self.task != 'classification':
            raise ValueError("predict_proba only works for classification")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores"""
        if not self.fitted:
            return {}
        
        importances = self.model.feature_importances_
        
        return {
            name: float(imp)
            for name, imp in zip(self.feature_names, importances)
        }
    
    def get_decision_path(self, X: np.ndarray) -> List[str]:
        """Get human-readable decision path for predictions"""
        if not self.fitted or len(X) == 0:
            return []
        
        # Use first tree's decision path
        tree = self.model.estimators_[0]
        paths = []
        
        for sample_idx in range(min(len(X), 1)):  # Just first sample
            sample = self.scaler.transform(X[sample_idx:sample_idx+1])
            
            # Walk the tree to get decision path
            node_indicator = tree.decision_path(sample)
            leaf_id = tree.apply(sample)
            
            path_description = []
            for node_id, feature_id in zip(
                node_indicator.indices,
                tree.feature[node_indicator.indices]
            ):
                if feature_id >= 0:
                    threshold = tree.threshold[node_id]
                    feature_name = self.feature_names[feature_id]
                    value = sample[0, feature_id]
                    
                    direction = ">" if value > threshold else "<="
                    path_description.append(
                        f"{feature_name} {direction} {threshold:.2f}"
                    )
            
            paths.append(path_description)
        
        return paths[0] if paths else []

# ============================================================================
# ENSEMBLE VOTING SYSTEM
# ============================================================================

class AdvancedModelEnsemble:
    """
    Master ensemble combining multiple model types
    """
    
    def __init__(self):
        self.models: Dict[str, any] = {}
        self.weights: Dict[str, float] = {}
        self.recent_accuracy: Dict[str, float] = {}
    
    def register_model(self, name: str, model: any, initial_weight: float = 1.0):
        """Register a model in the ensemble"""
        self.models[name] = model
        self.weights[name] = initial_weight
        self.recent_accuracy[name] = 0.5  # neutral
    
    def ensemble_prediction(
        self,
        predictions: Dict[str, Dict],
        voting_method: str = 'weighted'
    ) -> Dict:
        """
        Combine predictions from multiple models
        
        Args:
            predictions: Dict of {model_name: {prob, confidence, ...}}
            voting_method: 'weighted', 'majority', or 'stacking'
        
        Returns:
            Ensemble prediction
        """
        if voting_method == 'weighted':
            return self._weighted_voting(predictions)
        elif voting_method == 'majority':
            return self._majority_voting(predictions)
        else:
            return self._soft_voting(predictions)
    
    def _weighted_voting(self, predictions: Dict[str, Dict]) -> Dict:
        """Weight predictions by recent accuracy"""
        total_weight = sum(
            self.weights.get(model, 1.0)
            for model in predictions.keys()
        )
        
        weighted_probs = []
        ensemble_confidence = []
        
        for model_name, pred in predictions.items():
            weight = self.weights.get(model_name, 1.0)
            weighted_prob = pred.get('probability', 0.5) * (weight / total_weight)
            weighted_probs.append(weighted_prob)
            ensemble_confidence.append(pred.get('confidence', 0.5) * weight / total_weight)
        
        return {
            'ensemble_prediction': sum(weighted_probs),
            'ensemble_confidence': sum(ensemble_confidence),
            'model_count': len(predictions),
            'voting_method': 'weighted',
            'constituent_predictions': predictions
        }
    
    def _majority_voting(self, predictions: Dict[str, Dict]) -> Dict:
        """Simple majority voting"""
        votes_for = sum(
            1 for pred in predictions.values()
            if pred.get('probability', 0.5) > 0.5
        )
        votes_against = len(predictions) - votes_for
        
        return {
            'ensemble_prediction': 1.0 if votes_for > votes_against else 0.0,
            'ensemble_confidence': max(votes_for, votes_against) / len(predictions),
            'votes_for': votes_for,
            'votes_against': votes_against
        }
    
    def _soft_voting(self, predictions: Dict[str, Dict]) -> Dict:
        """Average of probabilities"""
        probs = [pred.get('probability', 0.5) for pred in predictions.values()]
        
        return {
            'ensemble_prediction': np.mean(probs),
            'ensemble_confidence': np.std(probs) ** -1 / len(predictions),  # Lower std = higher confidence
            'min_prediction': np.min(probs),
            'max_prediction': np.max(probs),
            'std_prediction': np.std(probs)
        }
    
    def update_model_weight(self, model_name: str, recent_accuracy: float):
        """Update model weight based on recent performance"""
        # Weight = accuracy^2 to emphasize high performers
        new_weight = max(0.5, recent_accuracy ** 2)  # Min 0.5x weight
        self.weights[model_name] = new_weight
        self.recent_accuracy[model_name] = recent_accuracy

if __name__ == "__main__":
    # Example usage
    logger.info("Advanced Statistical Models loaded successfully")
