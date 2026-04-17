"""
Advanced Confidence Scoring System
Implements sophisticated confidence calculation based on multiple factors
"""

import numpy as np
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AdvancedConfidenceScorer:
    """Advanced confidence scoring for sports predictions"""
    
    def __init__(self):
        self.confidence_weights = {
            'model_consensus': 0.25,
            'prediction_strength': 0.20,
            'data_quality': 0.15,
            'market_alignment': 0.15,
            'historical_accuracy': 0.10,
            'feature_stability': 0.10,
            'temporal_factors': 0.05
        }
        
        self.calibration_factor = 1.0  # Will be adjusted based on historical performance
    
    def calculate_confidence(self,
                           model_predictions: Dict[str, float],
                           prediction_data: Dict[str, Any],
                           market_data: Dict[str, Any],
                           historical_performance: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive confidence score
        
        Returns:
            Dict with confidence score and detailed breakdown
        """
        
        confidence_components = {}
        
        # 1. Model Consensus Score
        consensus_score = self._calculate_model_consensus(model_predictions)
        confidence_components['model_consensus'] = consensus_score
        
        # 2. Prediction Strength Score
        strength_score = self._calculate_prediction_strength(prediction_data)
        confidence_components['prediction_strength'] = strength_score
        
        # 3. Data Quality Score
        quality_score = self._calculate_data_quality(prediction_data)
        confidence_components['data_quality'] = quality_score
        
        # 4. Market Alignment Score
        alignment_score = self._calculate_market_alignment(prediction_data, market_data)
        confidence_components['market_alignment'] = alignment_score
        
        # 5. Historical Accuracy Score
        accuracy_score = self._calculate_historical_accuracy(historical_performance)
        confidence_components['historical_accuracy'] = accuracy_score
        
        # 6. Feature Stability Score
        stability_score = self._calculate_feature_stability(prediction_data)
        confidence_components['feature_stability'] = stability_score
        
        # 7. Temporal Factors Score
        temporal_score = self._calculate_temporal_factors(prediction_data)
        confidence_components['temporal_factors'] = temporal_score
        
        # Calculate weighted confidence
        raw_confidence = sum(
            score * self.confidence_weights[component]
            for component, score in confidence_components.items()
        )
        
        # Apply calibration factor
        calibrated_confidence = raw_confidence * self.calibration_factor
        
        # Ensure confidence is within reasonable bounds
        final_confidence = max(0.1, min(0.95, calibrated_confidence))
        
        # Determine confidence level
        if final_confidence >= 0.8:
            confidence_level = "Very High"
        elif final_confidence >= 0.7:
            confidence_level = "High"
        elif final_confidence >= 0.6:
            confidence_level = "Medium-High"
        elif final_confidence >= 0.5:
            confidence_level = "Medium"
        elif final_confidence >= 0.4:
            confidence_level = "Low-Medium"
        else:
            confidence_level = "Low"
        
        return {
            'confidence_score': final_confidence,
            'confidence_percentage': final_confidence * 100,
            'confidence_level': confidence_level,
            'components': confidence_components,
            'weights': self.confidence_weights,
            'calibration_factor': self.calibration_factor,
            'recommendations': self._generate_recommendations(confidence_components, final_confidence)
        }
    
    def _calculate_model_consensus(self, model_predictions: Dict[str, float]) -> float:
        """Calculate model consensus score"""
        if not model_predictions:
            return 0.5
        
        predictions = list(model_predictions.values())
        
        # Calculate agreement (lower std = higher agreement)
        mean_pred = np.mean(predictions)
        std_pred = np.std(predictions)
        
        # Convert std to agreement score (0-1)
        agreement_score = max(0, 1 - (std_pred * 2))  # Scale std to 0-1
        
        # Calculate prediction strength (how far from 0.5)
        strength = abs(mean_pred - 0.5) * 2
        
        # Consensus is combination of agreement and strength
        consensus = (agreement_score * 0.6) + (strength * 0.4)
        
        return min(1.0, max(0.0, consensus))
    
    def _calculate_prediction_strength(self, prediction_data: Dict[str, Any]) -> float:
        """Calculate prediction strength based on feature differences"""
        
        # ELO difference strength
        home_elo = prediction_data.get('home_elo', 1500)
        away_elo = prediction_data.get('away_elo', 1500)
        elo_diff = abs(home_elo - away_elo)
        elo_strength = min(1.0, elo_diff / 200)  # Normalize to 0-1
        
        # Form difference strength
        home_form = prediction_data.get('home_form', 0.5)
        away_form = prediction_data.get('away_form', 0.5)
        form_diff = abs(home_form - away_form)
        form_strength = form_diff * 2  # Scale to 0-1
        
        # Injury impact strength
        home_injuries = prediction_data.get('home_injury_impact', 0)
        away_injuries = prediction_data.get('away_injury_impact', 0)
        injury_diff = abs(home_injuries - away_injuries)
        injury_strength = min(1.0, injury_diff * 2)
        
        # H2H advantage strength
        home_h2h = prediction_data.get('h2h_home_winrate', 0.5)
        away_h2h = prediction_data.get('h2h_away_winrate', 0.5)
        h2h_diff = abs(home_h2h - away_h2h)
        h2h_strength = h2h_diff * 2
        
        # Combine strengths with weights
        total_strength = (
            elo_strength * 0.3 +
            form_strength * 0.3 +
            injury_strength * 0.2 +
            h2h_strength * 0.2
        )
        
        return min(1.0, max(0.0, total_strength))
    
    def _calculate_data_quality(self, prediction_data: Dict[str, Any]) -> float:
        """Calculate data quality score"""
        
        quality_factors = []
        
        # Check for missing/default values
        default_values = {
            'home_elo': 1500,
            'away_elo': 1500,
            'home_form': 0.5,
            'away_form': 0.5,
            'home_injury_impact': 0,
            'away_injury_impact': 0
        }
        
        for key, default_val in default_values.items():
            if key in prediction_data and prediction_data[key] != default_val:
                quality_factors.append(1.0)
            else:
                quality_factors.append(0.5)
        
        # Check for reasonable value ranges
        if 'home_elo' in prediction_data:
            elo = prediction_data['home_elo']
            if 1300 <= elo <= 1700:
                quality_factors.append(1.0)
            else:
                quality_factors.append(0.7)
        
        if 'home_form' in prediction_data:
            form = prediction_data['home_form']
            if 0.2 <= form <= 0.8:
                quality_factors.append(1.0)
            else:
                quality_factors.append(0.7)
        
        return np.mean(quality_factors) if quality_factors else 0.5
    
    def _calculate_market_alignment(self, prediction_data: Dict[str, Any], market_data: Dict[str, Any]) -> float:
        """Calculate market alignment score"""
        
        if not market_data or 'home_implied_prob' not in market_data:
            return 0.5
        
        # Get model prediction (assuming we have it in prediction_data)
        # This would need to be passed in from the ML service
        model_home_prob = prediction_data.get('model_home_prob', 0.5)
        market_home_prob = market_data['home_implied_prob']
        
        # Calculate alignment (lower difference = higher alignment)
        prob_diff = abs(model_home_prob - market_home_prob)
        alignment = max(0, 1 - (prob_diff * 2))  # Scale to 0-1
        
        # Bonus for strong market confidence
        market_confidence = abs(market_home_prob - 0.5) * 2
        if market_confidence > 0.3:  # Market shows strong preference
            alignment_bonus = 0.1
        else:
            alignment_bonus = 0
        
        return min(1.0, alignment + alignment_bonus)
    
    def _calculate_historical_accuracy(self, historical_performance: Optional[Dict[str, float]]) -> float:
        """Calculate historical accuracy score"""
        
        if not historical_performance:
            return 0.6  # Default moderate score
        
        # Get recent accuracy metrics
        recent_accuracy = historical_performance.get('recent_accuracy', 0.6)
        recent_precision = historical_performance.get('recent_precision', 0.6)
        recent_f1 = historical_performance.get('recent_f1', 0.6)
        
        # Calculate weighted average
        accuracy_score = (recent_accuracy * 0.4 + recent_precision * 0.3 + recent_f1 * 0.3)
        
        return min(1.0, max(0.0, accuracy_score))
    
    def _calculate_feature_stability(self, prediction_data: Dict[str, Any]) -> float:
        """Calculate feature stability score"""
        
        stability_factors = []
        
        # Check for extreme values that might indicate data issues
        extreme_checks = {
            'home_elo': (1300, 1700),
            'away_elo': (1300, 1700),
            'home_form': (0.1, 0.9),
            'away_form': (0.1, 0.9),
            'home_injury_impact': (0, 0.5),
            'away_injury_impact': (0, 0.5)
        }
        
        for key, (min_val, max_val) in extreme_checks.items():
            if key in prediction_data:
                value = prediction_data[key]
                if min_val <= value <= max_val:
                    stability_factors.append(1.0)
                else:
                    stability_factors.append(0.5)  # Penalize extreme values
        
        # Check for reasonable relationships between features
        if 'home_elo' in prediction_data and 'away_elo' in prediction_data:
            elo_diff = abs(prediction_data['home_elo'] - prediction_data['away_elo'])
            if elo_diff <= 300:  # Reasonable ELO difference
                stability_factors.append(1.0)
            else:
                stability_factors.append(0.7)
        
        return np.mean(stability_factors) if stability_factors else 0.5
    
    def _calculate_temporal_factors(self, prediction_data: Dict[str, Any]) -> float:
        """Calculate temporal factors score"""
        
        temporal_factors = []
        
        # Day of week factor (some days might have different patterns)
        day_of_week = prediction_data.get('day_of_week', 3)
        
        # Weekend games might have different dynamics
        if day_of_week in [5, 6]:  # Saturday, Sunday
            temporal_factors.append(0.9)
        else:
            temporal_factors.append(1.0)
        
        # Season progress factor
        season_progress = prediction_data.get('season_progress', 0.5)
        
        # Early and late season might be less predictable
        if 0.2 <= season_progress <= 0.8:
            temporal_factors.append(1.0)
        else:
            temporal_factors.append(0.9)
        
        # Time since last update (would need timestamp)
        # For now, assume recent data
        temporal_factors.append(1.0)
        
        return np.mean(temporal_factors) if temporal_factors else 0.5
    
    def _generate_recommendations(self, components: Dict[str, float], final_confidence: float) -> List[str]:
        """Generate recommendations based on confidence components"""
        
        recommendations = []
        
        # Low confidence recommendations
        if final_confidence < 0.5:
            recommendations.append("Consider additional data sources to improve prediction confidence")
        
        # Component-specific recommendations
        if components.get('model_consensus', 0) < 0.6:
            recommendations.append("Model disagreement detected - review individual model performance")
        
        if components.get('data_quality', 0) < 0.7:
            recommendations.append("Data quality concerns - verify input data accuracy")
        
        if components.get('prediction_strength', 0) < 0.5:
            recommendations.append("Weak prediction signals - teams appear evenly matched")
        
        if components.get('historical_accuracy', 0) < 0.6:
            recommendations.append("Recent model performance below expectations - consider retraining")
        
        if not recommendations:
            recommendations.append("All confidence factors within acceptable ranges")
        
        return recommendations
    
    def update_calibration_factor(self, actual_results: List[bool], predicted_confidences: List[float]):
        """Update calibration factor based on actual vs predicted results"""
        
        if len(actual_results) < 10:  # Need sufficient data
            return
        
        # Calculate calibration metrics
        predicted_probs = np.array(predicted_confidences)
        actual_results = np.array(actual_results)
        
        # Brier score
        brier_score = np.mean((predicted_probs - actual_results) ** 2)
        
        # Reliability (calibration plot)
        n_bins = 5
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]
        
        reliability = 0
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            in_bin = (predicted_probs > bin_lower) & (predicted_probs <= bin_upper)
            prop_in_bin = in_bin.mean()
            
            if prop_in_bin > 0:
                accuracy_in_bin = actual_results[in_bin].mean()
                avg_confidence_in_bin = predicted_probs[in_bin].mean()
                reliability += prop_in_bin * abs(avg_confidence_in_bin - accuracy_in_bin)
        
        # Update calibration factor based on reliability
        if reliability > 0.1:  # Poor calibration
            if brier_score > 0.25:  # Overconfident
                self.calibration_factor *= 0.9  # Reduce confidence
            else:  # Underconfident
                self.calibration_factor *= 1.1  # Increase confidence
        
        # Keep calibration factor within reasonable bounds
        self.calibration_factor = max(0.5, min(2.0, self.calibration_factor))
        
        logger.info(f"Updated calibration factor to {self.calibration_factor:.2f} based on {len(actual_results)} recent predictions")