"""
Ensemble Prediction Models
Multiple sophisticated models for sports predictions
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

class EnsemblePredictor:
    """Master ensemble combining all individual models"""
    
    def __init__(self):
        self.xgboost_model = None
        self.lightgbm_model = None
        self.neural_net_model = None
        self.linear_model = None
        self.weights = {
            'xgboost': 0.35,
            'lightgbm': 0.30,
            'neural_net': 0.25,
            'linear': 0.10
        }

    def predict(self, X: np.ndarray) -> Tuple[float, float]:
        """
        Make ensemble prediction
        Returns: (prediction, confidence)
        """
        predictions = {}
        confidences = {}
        
        # Get predictions from each model
        if self.xgboost_model:
            pred, conf = self._xgboost_predict(X)
            predictions['xgboost'] = pred
            confidences['xgboost'] = conf
        
        if self.lightgbm_model:
            pred, conf = self._lightgbm_predict(X)
            predictions['lightgbm'] = pred
            confidences['lightgbm'] = conf
        
        if self.neural_net_model:
            pred, conf = self._neural_net_predict(X)
            predictions['neural_net'] = pred
            confidences['neural_net'] = conf
        
        if self.linear_model:
            pred, conf = self._linear_predict(X)
            predictions['linear'] = pred
            confidences['linear'] = conf
        
        # Weighted ensemble
        ensemble_pred = np.average(
            list(predictions.values()),
            weights=[self.weights[k] for k in predictions.keys()]
        )
        
        ensemble_conf = np.average(
            list(confidences.values()),
            weights=[self.weights[k] for k in confidences.keys()]
        )
        
        return ensemble_pred, min(ensemble_conf, 1.0)

    def _xgboost_predict(self, X: np.ndarray) -> Tuple[float, float]:
        """XGBoost model prediction"""
        try:
            proba = self.xgboost_model.predict_proba(X)
            confidence = float(np.max(proba))
            prediction = float(proba[0][1])
            return prediction, confidence
        except Exception as e:
            logger.warning(f"XGBoost prediction error: {e}")
            return 0.5, 0.0

    def _lightgbm_predict(self, X: np.ndarray) -> Tuple[float, float]:
        """LightGBM model prediction"""
        try:
            proba = self.lightgbm_model.predict_proba(X)
            confidence = float(np.max(proba))
            prediction = float(proba[0][1])
            return prediction, confidence
        except Exception as e:
            logger.warning(f"LightGBM prediction error: {e}")
            return 0.5, 0.0

    def _neural_net_predict(self, X: np.ndarray) -> Tuple[float, float]:
        """Neural Network model prediction"""
        try:
            prediction = float(self.neural_net_model.predict(X)[0][0])
            confidence = abs(prediction - 0.5) * 2 + 0.5
            return prediction, confidence
        except Exception as e:
            logger.warning(f"Neural Net prediction error: {e}")
            return 0.5, 0.0

    def _linear_predict(self, X: np.ndarray) -> Tuple[float, float]:
        """Linear regression model prediction"""
        try:
            proba = self.linear_model.predict_proba(X)
            confidence = float(np.max(proba))
            prediction = float(proba[0][1])
            return prediction, confidence
        except Exception as e:
            logger.warning(f"Linear model prediction error: {e}")
            return 0.5, 0.0


def extract_features(match_data: Dict[str, Any]) -> np.ndarray:
    """
    Extract and engineer features from match data
    """
    features = []
    
    # Team strength metrics
    features.append(match_data.get('home_elo', 1500))
    features.append(match_data.get('away_elo', 1500))
    
    # Recent form (0-1 scale)
    features.append(match_data.get('home_form', 0.5))
    features.append(match_data.get('away_form', 0.5))
    
    # Home/away advantage
    features.append(match_data.get('home_advantage', 0.1))
    
    # Head-to-head history
    features.append(match_data.get('h2h_home_winrate', 0.5))
    features.append(match_data.get('h2h_away_winrate', 0.5))
    
    # Injuries impact
    features.append(match_data.get('home_injury_impact', 0))
    features.append(match_data.get('away_injury_impact', 0))
    
    # Player props specific
    features.append(match_data.get('player_season_avg', 0))
    features.append(match_data.get('player_recent_form', 0.5))
    features.append(match_data.get('opponent_defense_rating', 0))
    
    # Temporal features
    features.append(match_data.get('day_of_week', 3) / 7.0)
    features.append(match_data.get('season_progress', 0.5))
    
    return np.array(features).reshape(1, -1)


def generate_reasoning(
    prediction: float,
    confidence: float,
    match_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate human-readable reasoning for predictions
    """
    reasoning = []
    
    # Analyze factors based on confidence
    if match_data.get('home_form', 0) > 0.6:
        reasoning.append({
            'factor': 'Home team recent form strong',
            'impact': 'positive',
            'weight': 0.25
        })
    
    if match_data.get('away_injury_impact', 0) > 0.3:
        reasoning.append({
            'factor': 'Away team key injuries',
            'impact': 'negative',
            'weight': 0.20
        })
    
    if match_data.get('h2h_home_winrate', 0.5) > 0.65:
        reasoning.append({
            'factor': 'Historical h2h advantage home',
            'impact': 'positive',
            'weight': 0.15
        })
    
    if confidence > 0.75:
        reasoning.append({
            'factor': 'Model consensus strong',
            'impact': 'positive',
            'weight': 0.10
        })
    
    return {
        'reasoning_points': reasoning,
        'summary': f'Prediction based on ensemble analysis of {len(reasoning)} factors',
        'confidence_level': 'High' if confidence > 0.75 else 'Medium' if confidence > 0.50 else 'Low'
    }
