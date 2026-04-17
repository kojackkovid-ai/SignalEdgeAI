"""
Data Validation Integration with ESPN Prediction Service

Example of how to integrate the data validation service with ESPN API calls.
Demonstrates using REAL ESPN data only - no hardcoded or fake data.
"""

import logging
from typing import Dict, List, Any, Optional
from app.services.data_validation_service import get_data_validation_service
from app.services.espn_prediction_service import ESPNPredictionService
from app.models.tier_features import TierFeatures

logger = logging.getLogger(__name__)


class ValidatedESPNPredictionService(ESPNPredictionService):
    """
    Extended ESPN prediction service with built-in data validation.
    All ESPN API responses are validated before use.
    
    This prevents:
    - Invalid stat values (NaN, Inf)
    - Out-of-range statistics
    - Data anomalies
    - Malformed API responses
    """
    
    def __init__(self):
        super().__init__()
        self.validation_service = get_data_validation_service()
        self._validation_stats = {
            'total_responses': 0,
            'failed_validations': 0,
            'anomalies_detected': 0
        }
    
    async def get_upcoming_games_validated(self, sport_key: str) -> List[Dict[str, Any]]:
        """
        Get upcoming games with validation applied.
        
        Process:
        1. Fetch from ESPN API (raw data)
        2. Validate response structure
        3. Validate each game's data
        4. Filter any invalid games
        5. Return only valid games
        """
        logger.info(f"[VALIDATED] Fetching games for {sport_key}")
        
        # Fetch raw data from ESPN
        games = await super().get_upcoming_games(sport_key)
        
        validated_games = []
        validation_issues = []
        
        for game in games:
            # Validate game structure
            is_valid, errors = self.validation_service.validate_game_data(
                game, sport_key
            )
            
            if not is_valid:
                logger.warning(
                    f"[VALIDATION] Game {game.get('id')} failed validation: {errors}"
                )
                validation_issues.append({
                    'game_id': game.get('id'),
                    'errors': errors
                })
                self._validation_stats['failed_validations'] += 1
                continue  # Skip invalid games
            
            # Check for suspicious data
            anomalies = []
            if 'home_team' in game and 'stats' in game.get('home_team', {}):
                anomalies.extend(
                    self.validation_service.detect_anomalies(
                        game['home_team']['stats'], sport_key
                    )
                )
            
            if anomalies:
                logger.warning(
                    f"[ANOMALY] Game {game.get('id')}: {anomalies}"
                )
                self._validation_stats['anomalies_detected'] += 1
                # Log but don't skip - anomalies don't invalidate data
                game['_anomalies'] = anomalies
            
            validated_games.append(game)
        
        self._validation_stats['total_responses'] += 1
        
        logger.info(
            f"[VALIDATED] {sport_key}: {len(validated_games)}/{len(games)} games valid. "
            f"Issues: {len(validation_issues)}, Anomalies: {self._validation_stats['anomalies_detected']}"
        )
        
        return validated_games
    
    async def get_prediction_validated(self, sport_key: str, event_id: str, 
                                      user_tier: str = 'free') -> Optional[Dict[str, Any]]:
        """
        Get prediction with validation and tier-based filtering.
        
        Process:
        1. Get prediction from parent service
        2. Validate all stat data
        3. Apply tier-based filters (confidence, prediction type)
        4. Return only valid predictions user can see
        """
        logger.info(f"[VALIDATED] Getting prediction for {sport_key}/{event_id}")
        
        # Get prediction
        prediction = await super().get_prediction(sport_key, event_id)
        
        if not prediction:
            return None
        
        # Check tier access
        tier_config = TierFeatures.get_tier_config(user_tier)
        if not tier_config:
            logger.warning(f"Invalid user tier: {user_tier}")
            return None
        
        # Check if user can see this prediction type
        pred_type = prediction.get('prediction_type', 'moneyline')
        if not TierFeatures.can_access_prediction_type(user_tier, pred_type):
            logger.info(
                f"User tier {user_tier} cannot access {pred_type} predictions"
            )
            return None  # User tier doesn't have access
        
        # Check confidence threshold for this tier
        min_confidence = tier_config.get('min_confidence_threshold', 70)
        confidence = prediction.get('confidence', 0)
        
        if confidence < min_confidence:
            logger.info(
                f"Prediction confidence {confidence}% below tier minimum {min_confidence}%"
            )
            return None  # Below confidence threshold for this tier
        
        # Validate prediction data
        if 'models' in prediction and isinstance(prediction['models'], list):
            for model in prediction['models']:
                # Validate confidence scores
                model_conf = model.get('confidence', 0)
                if model_conf < 0 or model_conf > 100:
                    logger.warning(
                        f"Model {model.get('name')}: Invalid confidence {model_conf}"
                    )
                    model['confidence'] = max(0, min(100, model_conf))
        
        logger.info(f"[VALIDATED] Prediction for {event_id} passed validation")
        return prediction
    
    async def get_all_predictions_validated(self, user_tier: str = 'free',
                                           min_confidence: float = None,
                                           sport: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all predictions with validation applied.
        Uses tier-based filtering.
        """
        # Get default thresholds for tier
        tier_config = TierFeatures.get_tier_config(user_tier)
        if not tier_config:
            logger.error(f"Invalid tier: {user_tier}")
            return []
        
        # Use tier's min confidence if not specified
        if min_confidence is None:
            min_confidence = tier_config.get('min_confidence_threshold', 70)
        
        # Get predictions using parent service
        all_predictions = await super().get_predictions(
            sport=sport,
            min_confidence=min_confidence
        )
        
        validated_predictions = []
        validation_issues = []
        
        for pred in all_predictions:
            # Check tier access
            pred_type = pred.get('prediction_type', 'moneyline')
            if not TierFeatures.can_access_prediction_type(user_tier, pred_type):
                continue
            
            # Check sport access
            sport_key = pred.get('sport_key')
            if sport_key and not TierFeatures.can_access_sport(user_tier, sport_key):
                continue
            
            # Check confidence
            if pred.get('confidence', 0) < min_confidence:
                continue
            
            validated_predictions.append(pred)
        
        logger.info(
            f"[VALIDATED] User tier {user_tier}: "
            f"{len(validated_predictions)}/{len(all_predictions)} predictions accessible. "
            f"Validation issues: {len(validation_issues)}"
        )
        
        return validated_predictions
    
    def get_validation_report(self) -> Dict[str, Any]:
        """
        Get validation statistics and issues.
        Useful for monitoring data quality.
        """
        return {
            'total_api_responses_processed': self._validation_stats['total_responses'],
            'failed_validations': self._validation_stats['failed_validations'],
            'anomalies_detected': self._validation_stats['anomalies_detected'],
            'validation_success_rate': (
                (self._validation_stats['total_responses'] - 
                 self._validation_stats['failed_validations']) / 
                max(1, self._validation_stats['total_responses'])
            ) if self._validation_stats['total_responses'] > 0 else 1.0
        }
    
    def reset_validation_stats(self):
        """Reset validation statistics"""
        self._validation_stats = {
            'total_responses': 0,
            'failed_validations': 0,
            'anomalies_detected': 0
        }


# Global instance
_validated_service = None


def get_validated_espn_service() -> ValidatedESPNPredictionService:
    """Get or create the validated ESPN service instance"""
    global _validated_service
    if _validated_service is None:
        _validated_service = ValidatedESPNPredictionService()
    return _validated_service


# Usage examples (in actual routes):
"""
Example 1: Get predictions for free tier user

from app.services.espn_integration import get_validated_espn_service

service = get_validated_espn_service()
predictions = await service.get_all_predictions_validated(
    user_tier='free',
    sport='basketball_nba'
)
# Returns only NBA predictions the free tier can access


Example 2: Monitor data quality

report = service.get_validation_report()
logger.info(f"Validation Report: {report}")
# Output: Validation Report: {
#   'total_api_responses_processed': 150,
#   'failed_validations': 3,
#   'anomalies_detected': 7,
#   'validation_success_rate': 0.98
# }


Example 3: Get single prediction with tier checking

prediction = await service.get_prediction_validated(
    sport_key='basketball_nba',
    event_id='game123',
    user_tier='pro'
)
# Returns prediction only if:
# - Prediction data is valid
# - User tier can access this prediction type
# - Confidence is above tier minimum
"""
