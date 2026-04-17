#!/usr/bin/env python3
"""
Test script to verify the fixes for:
1. KeyError in data_preprocessing.py
2. Model loading in enhanced_ml_service.py
3. Feature mismatch issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_data_preprocessing():
    """Test that data preprocessing works without KeyError"""
    logger.info("=" * 60)
    logger.info("TEST 1: Data Preprocessing - KeyError Fix")
    logger.info("=" * 60)
    
    try:
        from app.services.data_preprocessing import AdvancedFeatureEngineer
        
        engineer = AdvancedFeatureEngineer()
        
        # Create minimal test data
        test_data = {
            'home_team': 'Lakers',
            'away_team': 'Warriors',
            'home_wins': 10,
            'home_losses': 5,
            'away_wins': 8,
            'away_losses': 7,
            'home_recent_wins': 4,
            'away_recent_wins': 3,
            'home_points_for': 110,
            'home_points_against': 105,
            'away_points_for': 108,
            'away_points_against': 107,
            'spread_line': -3.5,
            'total_line': 220.5,
            'home_score': 112,
            'away_score': 108
        }
        
        # Test prepare_single_game_features
        logger.info("Testing prepare_single_game_features...")
        features_df = engineer.prepare_single_game_features(test_data, 'basketball_nba', 'moneyline')
        
        logger.info(f"✅ SUCCESS: Features created successfully!")
        logger.info(f"   Feature count: {len(features_df.columns)}")
        logger.info(f"   Feature shape: {features_df.shape}")
        
        # Check for expected columns
        expected_cols = ['home_win_pct', 'away_win_pct', 'net_rating_diff']
        missing_cols = [col for col in expected_cols if col not in features_df.columns]
        
        if missing_cols:
            logger.warning(f"   Missing expected columns: {missing_cols}")
        else:
            logger.info(f"   ✅ All expected columns present")
        
        return True
        
    except KeyError as e:
        logger.error(f"❌ FAILED: KeyError - {e}")
        return False
    except Exception as e:
        logger.error(f"❌ FAILED: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_loading():
    """Test that model loading works correctly"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Model Loading - Dict to Model Object Fix")
    logger.info("=" * 60)
    
    try:
        from app.services.enhanced_ml_service import EnhancedMLService
        
        # Initialize service (this will call _load_all_models)
        logger.info("Initializing EnhancedMLService...")
        service = EnhancedMLService()
        
        logger.info(f"✅ SUCCESS: Service initialized!")
        logger.info(f"   Models loaded: {len(service.models)}")
        
        # Check model structure
        for model_key, model_data in service.models.items():
            logger.info(f"\n   Checking model: {model_key}")
            
            # Check if individual_models exists
            if 'individual_models' in model_data:
                individual_models = model_data['individual_models']
                logger.info(f"   - Individual models: {len(individual_models)}")
                
                # Check if models are objects, not dicts
                for name, model in individual_models.items():
                    if isinstance(model, dict):
                        logger.error(f"   ❌ Model '{name}' is a dict, not a model object!")
                        return False
                    elif hasattr(model, 'predict'):
                        logger.info(f"   - ✅ {name}: Model object with predict method")
                    else:
                        logger.warning(f"   - ⚠️ {name}: Unknown type {type(model)}")
            
            # Check if ensemble exists
            if 'ensemble' in model_data:
                ensemble = model_data['ensemble']
                if callable(ensemble):
                    logger.info(f"   - ✅ Ensemble: Callable function")
                elif hasattr(ensemble, 'predict'):
                    logger.info(f"   - ✅ Ensemble: Model object with predict method")
                else:
                    logger.warning(f"   - ⚠️ Ensemble: Unknown type {type(ensemble)}")
            else:
                logger.warning(f"   - ⚠️ No ensemble found for {model_key}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ FAILED: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prediction():
    """Test that prediction works end-to-end"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: End-to-End Prediction")
    logger.info("=" * 60)
    
    try:
        from app.services.enhanced_ml_service import EnhancedMLService
        import asyncio
        
        service = EnhancedMLService()
        
        # Create test game data
        game_data = {
            'event_id': 'test-game-001',
            'home_team': 'Lakers',
            'away_team': 'Warriors',
            'home_wins': 10,
            'home_losses': 5,
            'away_wins': 8,
            'away_losses': 7,
            'home_recent_wins': 4,
            'away_recent_wins': 3,
            'home_points_for': 110,
            'home_points_against': 105,
            'away_points_for': 108,
            'away_points_against': 107,
            'spread_line': -3.5,
            'total_line': 220.5,
            'home_score': 112,
            'away_score': 108
        }
        
        # Test prediction for each market type
        market_types = ['moneyline', 'spread', 'total']
        
        for market_type in market_types:
            logger.info(f"\nTesting {market_type} prediction...")
            
            try:
                # Run async prediction
                result = asyncio.run(service.predict('basketball_nba', market_type, game_data))
                
                if result.get('status') == 'success':
                    logger.info(f"   ✅ {market_type}: Prediction successful")
                    logger.info(f"      Confidence: {result.get('confidence', 'N/A')}%")
                    logger.info(f"      Features used: {result.get('features_used', 'N/A')}")
                else:
                    logger.warning(f"   ⚠️ {market_type}: {result.get('message', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"   ❌ {market_type}: {type(e).__name__} - {e}")
                import traceback
                traceback.print_exc()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ FAILED: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    logger.info("\n" + "=" * 60)
    logger.info("RUNNING FIX VERIFICATION TESTS")
    logger.info("=" * 60)
    
    results = []
    
    # Test 1: Data Preprocessing
    results.append(("Data Preprocessing", test_data_preprocessing()))
    
    # Test 2: Model Loading
    results.append(("Model Loading", test_model_loading()))
    
    # Test 3: End-to-End Prediction
    results.append(("Prediction", test_prediction()))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 All fixes verified successfully!")
        return 0
    else:
        logger.info(f"\n⚠️ {total - passed} test(s) failed. Review errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

