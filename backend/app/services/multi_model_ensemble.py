"""
Multi-Model Ensemble System
Week 5-7 Enhancement: Combine 7+ ML models with adaptive weighting
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ModelMetrics:
    """Metrics for a single model"""
    model_name: str
    sport_key: str
    
    recent_accuracy: float = 0.5
    calibration_error: float = 0.5
    prediction_confidence: float = 0.5
    daily_performance: List[float] = field(default_factory=list)
    
    last_updated: datetime = field(default_factory=datetime.utcnow)
    active: bool = True

@dataclass
class EnsembleConfig:
    """Configuration for ensemble voting"""
    min_models: int = 3  # Minimum models for ensemble
    max_models: int = 7  # Maximum models in ensemble
    confidence_threshold: float = 0.55  # Min confidence to vote
    weight_update_frequency: int = 1  # Update weights daily
    voting_method: str = 'weighted'  # weighted, majority, stacking

class EnsembleWeightCalculator:
    """Calculate optimal weights for ensemble models"""
    
    @staticmethod
    def calculate_weights(
        model_metrics: Dict[str, ModelMetrics],
        weight_config: Dict = None
    ) -> Dict[str, float]:
        """
        Calculate weights for each model based on recent performance
        
        Weight Components:
        - Recent Accuracy (50%): How often model predicts correctly
        - Calibration Quality (30%): How well confidence matches outcome
        - Prediction Confidence (20%): Model's confidence levels
        """
        config = weight_config or {
            'accuracy_weight': 0.50,
            'calibration_weight': 0.30,
            'confidence_weight': 0.20
        }
        
        weights = {}
        
        for model_name, metrics in model_metrics.items():
            if not metrics.active:
                weights[model_name] = 0.0
                continue
            
            # Normalize metrics to 0-1 range
            accuracy_score = metrics.recent_accuracy  # Already 0-1
            calibration_score = 1 - metrics.calibration_error  # Invert error
            confidence_score = metrics.prediction_confidence
            
            # Ensure all in 0-1 range
            accuracy_score = np.clip(accuracy_score, 0, 1)
            calibration_score = np.clip(calibration_score, 0, 1)
            confidence_score = np.clip(confidence_score, 0, 1)
            
            # Weighted combination
            combined_score = (
                accuracy_score * config['accuracy_weight'] +
                calibration_score * config['calibration_weight'] +
                confidence_score * config['confidence_weight']
            )
            
            # Square the score to emphasize strong performers
            # High performers get higher weights
            weights[model_name] = combined_score ** 1.5
        
        # Normalize weights to sum to number of active models
        total_weight = sum(w for w in weights.values() if w > 0)
        
        if total_weight > 0:
            active_count = len([w for w in weights.values() if w > 0])
            weights = {
                k: (v / total_weight) * active_count if v > 0 else 0
                for k, v in weights.items()
            }
        
        return weights

# ============================================================================
# MULTI-MODEL ENSEMBLE
# ============================================================================

class MultiModelEnsemble:
    """
    Master ensemble system combining multiple ML models
    Includes: XGBoost, Neural Network, Random Forest, Bayesian, ARIMA, Decision Trees
    """
    
    def __init__(
        self,
        sport_key: str,
        config: EnsembleConfig = None,
        db: AsyncSession = None
    ):
        self.sport_key = sport_key
        self.config = config or EnsembleConfig()
        self.db = db
        
        self.models: Dict[str, any] = {}
        self.model_metrics: Dict[str, ModelMetrics] = {}
        self.weights: Dict[str, float] = {}
        self.prediction_history: List[Dict] = []
    
    def register_model(
        self,
        model_name: str,
        model: any,
        sport_keys: List[str] = None
    ):
        """
        Register a model in the ensemble
        
        Args:
            model_name: Unique model identifier
            model: Actual model instance
            sport_keys: Sports this model supports (None = all)
        """
        if self.sport_key in (sport_keys or [self.sport_key]):
            self.models[model_name] = model
            self.model_metrics[model_name] = ModelMetrics(
                model_name=model_name,
                sport_key=self.sport_key
            )
            self.weights[model_name] = 1.0 / max(1, len(self.models))
            
            logger.info(f"Registered model: {model_name} for {self.sport_key}")
    
    async def make_ensemble_prediction(
        self,
        features: Dict,
        event_id: str = None,
        return_individual: bool = False
    ) -> Dict:
        """
        Make prediction using ensemble of models
        
        Args:
            features: Input features for prediction
            event_id: Event identifier for tracking
            return_individual: Include individual model predictions
        
        Returns:
            Ensemble prediction with confidence
        """
        # Get predictions from all active models
        individual_predictions = {}
        
        for model_name, model in self.models.items():
            if not self.model_metrics[model_name].active:
                continue
            
            try:
                # Get prediction from model
                pred = await self._get_model_prediction(model, features)
                
                individual_predictions[model_name] = {
                    'probability': pred.get('probability', 0.5),
                    'confidence': pred.get('confidence', 0.5),
                    'reasoning': pred.get('reasoning', [])
                }
            except Exception as e:
                logger.error(f"Model {model_name} prediction failed: {e}")
                self.model_metrics[model_name].active = False
        
        # Check if we have enough models
        if len(individual_predictions) < self.config.min_models:
            logger.warning(f"Ensemble has <{self.config.min_models} active models")
            return self._fallback_prediction()
        
        # Voting
        ensemble_result = self._ensemble_voting(
            individual_predictions,
            self.weights
        )
        
        # Add supporting data
        ensemble_result['sport_key'] = self.sport_key
        ensemble_result['event_id'] = event_id
        ensemble_result['model_count'] = len(individual_predictions)
        ensemble_result['prediction_time'] = datetime.utcnow().isoformat()
        
        if return_individual:
            ensemble_result['individual_predictions'] = individual_predictions
        
        # Track prediction
        self.prediction_history.append(ensemble_result)
        
        return ensemble_result
    
    def _ensemble_voting(
        self,
        predictions: Dict[str, Dict],
        weights: Dict[str, float]
    ) -> Dict:
        """
        Combine predictions from multiple models using weighted voting
        """
        if self.config.voting_method == 'weighted':
            return self._weighted_voting(predictions, weights)
        elif self.config.voting_method == 'majority':
            return self._majority_voting(predictions)
        elif self.config.voting_method == 'stacking':
            return self._stacking_voting(predictions, weights)
        else:
            return self._soft_voting(predictions)
    
    def _weighted_voting(
        self,
        predictions: Dict[str, Dict],
        weights: Dict[str, float]
    ) -> Dict:
        """Weight predictions by model strength"""
        weighted_probs = []
        weighted_confidences = []
        total_weight = 0
        model_votes = []
        
        for model_name, pred in predictions.items():
            weight = weights.get(model_name, 0)
            
            if weight > 0:
                weighted_prob = pred['probability'] * weight
                weighted_confidence = pred['confidence'] * weight
                
                weighted_probs.append(weighted_prob)
                weighted_confidences.append(weighted_confidence)
                total_weight += weight
                
                model_votes.append({
                    'model': model_name,
                    'vote': pred['probability'],
                    'weight': weight
                })
        
        if total_weight == 0:
            return {'probability': 0.5, 'confidence': 0.5, 'voting_method': 'weighted'}
        
        ensemble_prob = sum(weighted_probs)
        ensemble_confidence = sum(weighted_confidences) / total_weight
        
        return {
            'probability': ensemble_prob,
            'confidence': ensemble_confidence,
            'voting_method': 'weighted',
            'model_votes': model_votes,
            'total_weight': total_weight,
            'agreement_score': self._calculate_agreement(predictions)
        }
    
    def _majority_voting(self, predictions: Dict[str, Dict]) -> Dict:
        """Simple majority voting"""
        votes_yes = sum(
            1 for p in predictions.values()
            if p['probability'] > 0.5
        )
        votes_no = len(predictions) - votes_yes
        
        confidence = max(votes_yes, votes_no) / len(predictions)
        
        return {
            'probability': 1.0 if votes_yes > votes_no else 0.0,
            'confidence': confidence,
            'voting_method': 'majority',
            'votes_yes': votes_yes,
            'votes_no': votes_no,
            'agreement_score': confidence
        }
    
    def _soft_voting(self, predictions: Dict[str, Dict]) -> Dict:
        """Average of probabilities"""
        probs = [p['probability'] for p in predictions.values()]
        confidences = [p['confidence'] for p in predictions.values()]
        
        ensemble_prob = np.mean(probs)
        ensemble_confidence = np.mean(confidences)
        
        # Agreement = inverse of standard deviation
        prob_std = np.std(probs)
        agreement = 1 - min(prob_std, 0.5) / 0.5
        
        return {
            'probability': ensemble_prob,
            'confidence': ensemble_confidence,
            'voting_method': 'soft',
            'probability_std': prob_std,
            'agreement_score': agreement
        }
    
    def _stacking_voting(
        self,
        predictions: Dict[str, Dict],
        weights: Dict[str, float]
    ) -> Dict:
        """
        Stacking voting - use meta-learner to combine predictions
        (Simplified version)
        """
        # For now, use weighted voting as base stacking
        # In production, train a separate meta-model
        return self._weighted_voting(predictions, weights)
    
    def _calculate_agreement(self, predictions: Dict[str, Dict]) -> float:
        """
        Calculate agreement score among models
        Higher = models agree more
        """
        if len(predictions) < 2:
            return 1.0
        
        probs = np.array([p['probability'] for p in predictions.values()])
        
        # Standard deviation of predictions
        prob_std = np.std(probs)
        
        # Convert std to agreement (0-1, where 1 = perfect agreement)
        agreement = 1 - min(prob_std, 0.5) / 0.5
        
        return agreement
    
    async def update_weights(self, lookback_days: int = 7):
        """
        Update model weights based on recent performance
        Should be called daily
        """
        # Get recent predictions
        recent_predictions = self.prediction_history[-1000:]  # Last 1000 predictions
        
        if not recent_predictions:
            logger.warning("No recent predictions for weight update")
            return
        
        # Calculate recent accuracy for each model
        for model_name in self.models.keys():
            # Count how often this model's prediction was correct
            correct = 0
            total = 0
            
            for pred in recent_predictions:
                if 'individual_predictions' in pred:
                    model_pred = pred['individual_predictions'].get(model_name)
                    # This is simplified - in production, compare to actual outcomes
                    if model_pred:
                        total += 1
            
            if total > 0:
                accuracy = correct / total
                self.model_metrics[model_name].recent_accuracy = accuracy
        
        # Recalculate weights
        calculator = EnsembleWeightCalculator()
        self.weights = calculator.calculate_weights(self.model_metrics)
        
        logger.info(f"Updated ensemble weights for {self.sport_key}")
    
    async def get_model_diagnostics(self, model_name: str) -> Dict:
        """Get detailed diagnostics for a specific model"""
        if model_name not in self.model_metrics:
            return {}
        
        metrics = self.model_metrics[model_name]
        
        return {
            'model_name': model_name,
            'active': metrics.active,
            'recent_accuracy': metrics.recent_accuracy,
            'calibration_error': metrics.calibration_error,
            'prediction_confidence': metrics.prediction_confidence,
            'weight': self.weights.get(model_name, 0),
            'last_updated': metrics.last_updated.isoformat(),
            'daily_performance': metrics.daily_performance[-7:]  # Last 7 days
        }
    
    async def _get_model_prediction(
        self,
        model: any,
        features: Dict
    ) -> Dict:
        """
        Get prediction from individual model
        Handles different model types
        """
        # This is a simplified version - actual implementation
        # would handle different model architectures
        
        try:
            # Try to call predict method
            if hasattr(model, 'predict'):
                result = model.predict(features)
                return {
                    'probability': result if isinstance(result, (int, float)) else 0.5,
                    'confidence': 0.5,
                    'reasoning': []
                }
            else:
                return {'probability': 0.5, 'confidence': 0.3, 'reasoning': ['Model unavailable']}
        
        except Exception as e:
            logger.error(f"Model prediction failed: {e}")
            return {'probability': 0.5, 'confidence': 0.2, 'reasoning': [str(e)]}
    
    def _fallback_prediction(self) -> Dict:
        """Return neutral prediction when ensemble is unavailable"""
        return {
            'probability': 0.5,
            'confidence': 0.5,
            'voting_method': 'fallback',
            'model_count': 0,
            'warning': 'Insufficient models available'
        }
    
    async def daily_calibration_update(self):
        """
        Run daily calibration to ensure model confidence is well-calibrated
        """
        # Group recent predictions by confidence bucket
        buckets = {
            '50_60': [],
            '60_70': [],
            '70_80': [],
            '80_90': [],
            '90_100': []
        }
        
        for pred in self.prediction_history[-500:]:  # Last 500
            confidence = pred.get('confidence', 0.5)
            
            if 0.50 <= confidence < 0.60:
                buckets['50_60'].append(pred)
            elif 0.60 <= confidence < 0.70:
                buckets['60_70'].append(pred)
            elif 0.70 <= confidence < 0.80:
                buckets['70_80'].append(pred)
            elif 0.80 <= confidence < 0.90:
                buckets['80_90'].append(pred)
            else:
                buckets['90_100'].append(pred)
        
        # Calculate calibration error for each bucket
        calibration_errors = {}
        
        for bucket_name, predictions in buckets.items():
            if not predictions:
                continue
            
            # In production, compare to actual outcomes
            # For now, just record bucket stats
            confidence_level = float(bucket_name.split('_')[0]) / 100
            
            calibration_errors[bucket_name] = {
                'confidence_level': confidence_level,
                'prediction_count': len(predictions),
                'actual_accuracy': 0.5  # Placeholder
            }
        
        # Update overall calibration metrics
        for model_name in self.model_metrics.keys():
            # Simple calibration error calculation
            self.model_metrics[model_name].calibration_error = np.mean(
                [abs(c['confidence_level'] - c['actual_accuracy']) 
                 for c in calibration_errors.values()]
            )

if __name__ == "__main__":
    print("Multi-Model Ensemble System loaded")
