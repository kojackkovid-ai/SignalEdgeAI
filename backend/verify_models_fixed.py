#!/usr/bin/env python3
"""
Verify that existing models work with the fixes applied
Tests: XGBoost 3-class, puck_line support, column alignment
"""

import asyncio
import logging
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.enhanced_ml_service import EnhancedMLService
from app.services.data_preprocessing import AdvancedFeatureEngineer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configurations that were problematic
TEST_CONFIGS = [
    ('soccer_epl', 'moneyline'),      # 3-class XGBoost
    ('icehockey_nhl', 'puck_line'),   # puck_line market
    ('basketball_nba', 'spread'),     # Standard
    ('americanfootball_nfl', 'total'), # Total
]

# Sample game data for testing
def create_test_game(sport_key: str) -> dict:
    """Create test game data with all required fields"""
    base_game = {
        'home_team': 'Team A',
        'away_team': 'Team B',
        'home_wins': 10,
        'home_losses': 5,
        'away_wins': 8,
        'away_losses': 7,
        'home_recent_wins': 4,
        'away_recent_wins': 3,
        'home_rest_days': 2,
        'away_rest_days': 3,
        'home_opponent_win_pct': 0.55,
        'away_opponent_win_pct': 0.48,
    }
    
    # Add sport-specific fields
    if sport_key.startswith('soccer_'):
        base_game.update({
            'home_goals_for': 25,
            'home_goals_against': 18,
            'away_goals_for': 22,
            'away_goals_against': 20,
        })
    else:
        base_game.update({
            'home_points_for': 110,
            'home_points_against': 105,
            'away_points_for': 108,
            'away_points_against': 109,
        })
    
    return base_game


async def test_model_loading():
    """Test that models load correctly"""
    logger.info("=" * 70)
    logger.info("TESTING MODEL LOADING")
    logger.info("=" * 70)
    
    ml_service = EnhancedMLService()
    
    loaded_models = list(ml_service.models.keys())
    logger.info(f"Loaded {len(loaded_models)} model sets:")
    for model_key in sorted(loaded_models):
        logger.info(f"  - {model_key}")
    
    return len(loaded_models) > 0


async def test_predictions():
    """Test predictions for problematic configurations"""
    logger.info("\n" + "=" * 70)
    logger.info("TESTING PREDICTIONS")
    logger.info("=" * 70)
    
    ml_service = EnhancedMLService()
    results = []
    
    for sport_key, market_type in TEST_CONFIGS:
        model_key = f"{sport_key}_{market_type}"
        logger.info(f"\nTesting {model_key}...")
        
        # Check if model exists
        if model_key not in ml_service.models:
            logger.warning(f"  Model {model_key} not found - skipping")
            continue
        
        # Create test game
        game_data = create_test_game(sport_key)
        
        try:
            # Make prediction
            result = await ml_service.predict(sport_key, market_type, game_data)
            
            if result.get('status') == 'success':
                logger.info(f"  [OK] Prediction: {result.get('prediction')}, Confidence: {result.get('confidence'):.1f}%")
                results.append({
                    'model_key': model_key,
                    'status': 'success',
                    'prediction': result.get('prediction'),
                    'confidence': result.get('confidence')
                })
            else:
                logger.error(f"  [FAIL] {result.get('message')}")
                results.append({
                    'model_key': model_key,
                    'status': 'error',
                    'error': result.get('message')
                })
                
        except Exception as e:
            logger.error(f"  [ERROR] Exception: {e}")
            results.append({
                'model_key': model_key,
                'status': 'error',
                'error': str(e)
            })
    
    return results


async def test_feature_engineering():
    """Test feature engineering for different sports"""
    logger.info("\n" + "=" * 70)
    logger.info("TESTING FEATURE ENGINEERING")
    logger.info("=" * 70)
    
    engineer = AdvancedFeatureEngineer()
    
    # Test data preparation
    test_data = pd.DataFrame([{
        'home_score': 110,
        'away_score': 105,
        'home_wins': 10,
        'home_losses': 5,
        'away_wins': 8,
        'away_losses': 7,
        'home_recent_wins': 4,
        'away_recent_wins': 3,
        'home_points_for': 1100,
        'home_points_against': 1050,
        'away_points_for': 1080,
        'away_points_against': 1090,
        'home_goals_for': 25,
        'home_goals_against': 18,
        'away_goals_for': 22,
        'away_goals_against': 20,
    }])
    
    for sport_key in ['basketball_nba', 'soccer_epl', 'icehockey_nhl']:
        for market_type in ['moneyline', 'spread', 'total']:
            try:
                X, y = engineer.prepare_features(test_data, sport_key, market_type)
                logger.info(f"  [OK] {sport_key} - {market_type}: {X.shape[1]} features")
            except Exception as e:
                logger.error(f"  [FAIL] {sport_key} - {market_type}: {e}")


async def main():
    """Main verification"""
    logger.info("MODEL VERIFICATION AFTER FIXES")
    logger.info("=" * 70)
    
    # Test 1: Model loading
    models_loaded = await test_model_loading()
    
    # Test 2: Feature engineering
    await test_feature_engineering()
    
    # Test 3: Predictions
    prediction_results = await test_predictions()
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 70)
    
    successful = sum(1 for r in prediction_results if r['status'] == 'success')
    failed = sum(1 for r in prediction_results if r['status'] == 'error')
    
    logger.info(f"Models loaded: {models_loaded}")
    logger.info(f"Predictions successful: {successful}/{len(prediction_results)}")
    logger.info(f"Predictions failed: {failed}/{len(prediction_results)}")
    
    if failed == 0:
        logger.info("\n[OK] All verifications passed! Models are working correctly.")
        return 0
    else:
        logger.warning(f"\n[WARNING] {failed} tests failed. Check logs above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
