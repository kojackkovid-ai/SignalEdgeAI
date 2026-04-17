"""
Dynamic Model Weighting System
Automatically adjusts ensemble weights based on real prediction accuracy from ESPN data
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelOptimizer:
    """
    Dynamically adjusts model weights based on historical prediction accuracy.
    Uses real game outcomes from ESPN to track which models perform best.
    """
    
    # Default weights (will be adjusted over time)
    DEFAULT_WEIGHTS = {
        'xgboost': 0.35,
        'lightgbm': 0.30,
        'neural_net': 0.25,
        'linear_regression': 0.10
    }
    
    # Sport-specific weights (can be different per sport)
    DEFAULT_SPORT_WEIGHTS = {
        'nba': {'xgboost': 0.35, 'lightgbm': 0.30, 'neural_net': 0.25, 'linear_regression': 0.10},
        'nfl': {'xgboost': 0.40, 'lightgbm': 0.25, 'neural_net': 0.25, 'linear_regression': 0.10},
        'mlb': {'xgboost': 0.30, 'lightgbm': 0.35, 'neural_net': 0.25, 'linear_regression': 0.10},
        'nhl': {'xgboost': 0.30, 'lightgbm': 0.35, 'neural_net': 0.25, 'linear_regression': 0.10},
        'soccer': {'xgboost': 0.25, 'lightgbm': 0.30, 'neural_net': 0.35, 'linear_regression': 0.10},
        'ncaab': {'xgboost': 0.35, 'lightgbm': 0.30, 'neural_net': 0.25, 'linear_regression': 0.10}
    }
    
    def __init__(
        self,
        decay_factor: float = 0.95,
        min_samples: int = 10,
        weight_change_rate: float = 0.2,
        weights_file: Optional[str] = None
    ):
        """
        Initialize Model Optimizer.
        
        Args:
            decay_factor: Recent results weighted more (0-1). Higher = more weight on recent.
            min_samples: Minimum samples before adjusting weights
            weight_change_rate: Maximum weight change per update (0-1)
            weights_file: Path to persist weights
        """
        self.decay_factor = decay_factor
        self.min_samples = min_samples
        self.weight_change_rate = weight_change_rate
        
        # Track prediction results: {model_name: [{correct, confidence, sport, timestamp}]}
        self.prediction_results: Dict[str, List[Dict]] = defaultdict(list)
        
        # Current weights per sport
        self.current_weights: Dict[str, Dict[str, float]] = {}
        
        # Initialize with defaults
        for sport, weights in self.DEFAULT_SPORT_WEIGHTS.items():
            self.current_weights[sport] = weights.copy()
        self.current_weights['default'] = self.DEFAULT_WEIGHTS.copy()
        
        # Load persisted weights if available
        if weights_file:
            self.load_weights(weights_file)
    
    def record_prediction(
        self,
        model_name: str,
        sport: str,
        predicted_outcome: str,
        actual_outcome: str,
        confidence: float,
        game_id: Optional[str] = None
    ):
        """
        Record a prediction result for model performance tracking.
        
        Args:
            model_name: Name of the model (xgboost, lightgbm, etc.)
            sport: Sport key (nba, nfl, etc.)
            predicted_outcome: What was predicted
            actual_outcome: What actually happened
            confidence: Model's confidence (0-100)
            game_id: Optional game identifier
        """
        # Determine if prediction was correct
        predicted_outcome = predicted_outcome.lower().strip()
        actual_outcome = actual_outcome.lower().strip()
        
        # Handle different prediction formats
        correct = self._check_correctness(predicted_outcome, actual_outcome)
        
        result = {
            'timestamp': datetime.utcnow(),
            'sport': sport,
            'predicted': predicted_outcome,
            'actual': actual_outcome,
            'correct': correct,
            'confidence': confidence,
            'game_id': game_id,
            'accuracy': 1.0 if correct else 0.0
        }
        
        self.prediction_results[model_name].append(result)
        
        # Keep only last 1000 results per model
        if len(self.prediction_results[model_name]) > 1000:
            self.prediction_results[model_name] = self.prediction_results[model_name][-1000:]
        
        logger.debug(
            f"Recorded prediction: {model_name} [{sport}] "
            f"predicted={predicted_outcome}, actual={actual_outcome}, correct={correct}"
        )
    
    def _check_correctness(self, predicted: str, actual: str) -> bool:
        """Check if prediction was correct."""
        # Direct match
        if predicted == actual:
            return True
        
        # Handle "team wins" format
        if 'win' in predicted and 'win' in actual:
            pred_team = predicted.replace(' win', '').strip()
            act_team = actual.replace(' win', '').strip()
            if pred_team == act_team:
                return True
        
        # Handle over/under
        if predicted.startswith(('over', 'under')) and actual.startswith(('over', 'under')):
            return predicted == actual
        
        return False
    
    def calculate_weights(
        self,
        sport: Optional[str] = None,
        time_window_days: int = 30,
        use_sport_specific: bool = True
    ) -> Dict[str, float]:
        """
        Calculate optimal weights based on recent performance.
        
        Uses exponential decay to weight recent results more heavily.
        
        Args:
            sport: Optional sport to get weights for (None = use default)
            time_window_days: How far back to look
            use_sport_specific: Use sport-specific weights if available
            
        Returns:
            Dict of model_name -> weight
        """
        # Determine which weights to use
        if use_sport_specific and sport:
            sport_key = self._normalize_sport(sport)
            if sport_key in self.current_weights:
                base_weights = self.current_weights[sport_key]
            else:
                base_weights = self.current_weights.get('default', self.DEFAULT_WEIGHTS)
        else:
            base_weights = self.current_weights.get('default', self.DEFAULT_WEIGHTS)
        
        # Get cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
        
        # Calculate weighted accuracy for each model
        model_performances = {}
        
        for model_name, results in self.prediction_results.items():
            # Filter by time window
            recent_results = [
                r for r in results
                if r['timestamp'] >= cutoff_date
            ]
            
            if sport:
                recent_results = [
                    r for r in recent_results
                    if self._normalize_sport(r['sport']) == self._normalize_sport(sport)
                ]
            
            # Need minimum samples
            if len(recent_results) < self.min_samples:
                model_performances[model_name] = {
                    'accuracy': 0.5,
                    'samples': len(recent_results),
                    'use_default': True
                }
                continue
            
            # Calculate weighted accuracy (exponential decay)
            weighted_sum = 0.0
            weight_total = 0.0
            
            for result in recent_results:
                # More recent = higher weight
                age_days = (datetime.utcnow() - result['timestamp']).total_seconds() / 86400
                weight = self.decay_factor ** age_days
                
                weighted_sum += result['accuracy'] * weight
                weight_total += weight
            
            accuracy = weighted_sum / weight_total if weight_total > 0 else 0.5
            
            model_performances[model_name] = {
                'accuracy': accuracy,
                'samples': len(recent_results),
                'use_default': False
            }
        
        # Check if we have enough data
        valid_models = [m for m, p in model_performances.items() if not p['use_default']]
        
        if len(valid_models) < 2:
            logger.info("Insufficient data for dynamic weighting, using defaults")
            return base_weights.copy()
        
        # Normalize to weights
        total_accuracy = sum(p['accuracy'] for p in model_performances.values())
        
        if total_accuracy == 0:
            logger.warning("All models have 0 accuracy, using defaults")
            return base_weights.copy()
        
        # Calculate new weights based on accuracy
        raw_weights = {
            model: p['accuracy'] / total_accuracy
            for model, p in model_performances.items()
        }
        
        # Smooth transition (blend with current weights)
        new_weights = {}
        for model in base_weights.keys():
            current = base_weights.get(model, 0.25)
            calculated = raw_weights.get(model, 0.25)
            
            # Apply weight change rate limit
            raw_change = calculated - current
            max_change = self.weight_change_rate
            
            if abs(raw_change) > max_change:
                new_weight = current + (max_change if raw_change > 0 else -max_change)
            else:
                new_weight = calculated
            
            new_weights[model] = max(0.05, min(0.60, new_weight))  # Clamp between 5-60%
        
        # Re-normalize to sum to 1
        total = sum(new_weights.values())
        new_weights = {k: v/total for k, v in new_weights.items()}
        
        # Store for future use
        if sport:
            sport_key = self._normalize_sport(sport)
            self.current_weights[sport_key] = new_weights
        else:
            self.current_weights['default'] = new_weights
        
        logger.info(
            f"Updated model weights: {new_weights} "
            f"(based on {sum(p['samples'] for p in model_performances.values())} samples)"
        )
        
        return new_weights
    
    def _normalize_sport(self, sport: str) -> str:
        """Normalize sport key."""
        sport = sport.lower().strip()
        
        # Map common variations
        sport_map = {
            'basketball_nba': 'nba',
            'basketball_ncaa': 'ncaab',
            'americanfootball_nfl': 'nfl',
            'baseball_mlb': 'mlb',
            'icehockey_nhl': 'nhl',
            'soccer_epl': 'soccer',
            'soccer_mls': 'soccer',
            'soccer': 'soccer'
        }
        
        return sport_map.get(sport, sport)
    
    def get_performance_report(
        self,
        sport: Optional[str] = None,
        time_window_days: int = 30
    ) -> Dict:
        """
        Get detailed performance report for all models.
        
        Args:
            sport: Optional sport filter
            time_window_days: How far back to look
            
        Returns:
            Dict with performance metrics per model
        """
        cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'time_window_days': time_window_days,
            'sport': sport or 'all',
            'models': {}
        }
        
        for model_name, results in self.prediction_results.items():
            # Filter by time window
            recent = [
                r for r in results
                if r['timestamp'] >= cutoff_date
            ]
            
            if sport:
                recent = [
                    r for r in recent
                    if self._normalize_sport(r['sport']) == self._normalize_sport(sport)
                ]
            
            if not recent:
                continue
            
            correct = sum(1 for r in recent if r['correct'])
            total = len(recent)
            
            # Calculate metrics
            accuracy = correct / total if total > 0 else 0
            avg_confidence = sum(r['confidence'] for r in recent) / total
            
            # Calculate calibration (confidence vs actual accuracy)
            high_conf_correct = sum(1 for r in recent if r['confidence'] >= 70 and r['correct'])
            high_conf_total = sum(1 for r in recent if r['confidence'] >= 70)
            calibration = high_conf_correct / high_conf_total if high_conf_total > 0 else 0
            
            report['models'][model_name] = {
                'total_predictions': total,
                'correct': correct,
                'accuracy': round(accuracy * 100, 1),
                'avg_confidence': round(avg_confidence, 1),
                'calibration': round(calibration * 100, 1),
                'high_confidence_correct_pct': round(
                    (high_conf_correct / high_conf_total * 100) if high_conf_total > 0 else 0, 1
                ),
                'last_prediction': recent[-1]['timestamp'].isoformat() if recent else None
            }
        
        # Add current weights
        if sport:
            sport_key = self._normalize_sport(sport)
            report['current_weights'] = self.current_weights.get(
                sport_key,
                self.current_weights.get('default', self.DEFAULT_WEIGHTS)
            )
        else:
            report['current_weights'] = self.current_weights.get('default', self.DEFAULT_WEIGHTS)
        
        return report
    
    def get_best_model(self, sport: Optional[str] = None) -> Tuple[str, float]:
        """
        Get the best performing model for a sport.
        
        Returns:
            Tuple of (model_name, accuracy)
        """
        report = self.get_performance_report(sport=sport, time_window_days=30)
        
        if not report['models']:
            return ('xgboost', 0.5)  # Default
        
        best_model = max(
            report['models'].items(),
            key=lambda x: x[1]['accuracy']
        )
        
        return best_model[0], best_model[1]['accuracy']
    
    def get_ensemble_prediction(
        self,
        individual_predictions: Dict[str, float],
        sport: Optional[str] = None
    ) -> Dict:
        """
        Combine individual model predictions using dynamic weights.
        
        Args:
            individual_predictions: {model_name: probability}
            sport: Sport for weight selection
            
        Returns:
            Dict with combined prediction and confidence
        """
        # Get weights
        weights = self.calculate_weights(sport=sport)
        
        # Calculate weighted average
        weighted_sum = 0.0
        weight_total = 0.0
        
        for model_name, prob in individual_predictions.items():
            weight = weights.get(model_name, 0.25)
            weighted_sum += prob * weight
            weight_total += weight
        
        if weight_total > 0:
            combined_prob = weighted_sum / weight_total
        else:
            combined_prob = 0.5
        
        # Calculate confidence based on model agreement
        probs = list(individual_predictions.values())
        if len(probs) > 1:
            # Low standard deviation = high agreement = higher confidence
            import statistics
            std_dev = statistics.stdev(probs) if len(probs) > 1 else 0
            agreement_factor = max(0.5, 1 - std_dev)
        else:
            agreement_factor = 0.7
        
        # Final confidence
        confidence = combined_prob * agreement_factor * 100
        
        return {
            'combined_probability': round(combined_prob * 100, 1),
            'confidence': round(min(95, max(40, confidence)), 1),
            'weights_used': weights,
            'models_agreed': agreement_factor > 0.7,
            'sport': sport
        }
    
    def save_weights(self, filepath: str):
        """Save current weights to file."""
        data = {
            'current_weights': self.current_weights,
            'saved_at': datetime.utcnow().isoformat()
        }
        
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved model weights to {filepath}")
    
    def load_weights(self, filepath: str):
        """Load weights from file."""
        path = Path(filepath)
        
        if not path.exists():
            logger.warning(f"Weights file not found: {filepath}")
            return
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            if 'current_weights' in data:
                self.current_weights = data['current_weights']
                logger.info(f"Loaded model weights from {filepath}")
        except Exception as e:
            logger.error(f"Error loading weights: {e}")


# Global instance
model_optimizer = ModelOptimizer()
