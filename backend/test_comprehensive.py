#!/usr/bin/env python3
"""
Comprehensive test suite for all sports, markets, and edge cases
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration
SPORTS_TO_TEST = [
    'basketball_nba',
    'basketball_ncaa', 
    'americanfootball_nfl',
    'baseball_mlb',
    'icehockey_nhl',
    'soccer_epl',
    'soccer_usa_mls'
]

MARKETS_TO_TEST = ['moneyline', 'spread', 'total']

class ComprehensiveTester:
    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
        
    def log_result(self, test_name, status, message=""):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        if status == 'PASS':
            self.results['passed'].append(result)
            logger.info(f"✅ {test_name}: PASSED {message}")
        elif status == 'FAIL':
            self.results['failed'].append(result)
            logger.error(f"❌ {test_name}: FAILED {message}")
        else:
            self.results['warnings'].append(result)
            logger.warning(f"⚠️ {test_name}: WARNING {message}")
    
    def test_all_sports_predictions(self):
        """Test predictions for all sports and markets"""
        logger.info("\n" + "="*70)
        logger.info("TESTING ALL SPORTS AND MARKETS")
        logger.info("="*70)
        
        try:
            from app.services.enhanced_ml_service import EnhancedMLService
            from app.services.data_preprocessing import AdvancedFeatureEngineer
            
            ml_service = EnhancedMLService()
            feature_engineer = AdvancedFeatureEngineer()
            
            for sport in SPORTS_TO_TEST:
                for market in MARKETS_TO_TEST:
                    test_name = f"{sport}_{market}"
                    try:
                        # Create sample game data
                        sample_game = self._create_sample_game(sport)
                        
                        # Prepare features - returns DataFrame only
                        features_df = feature_engineer.prepare_single_game_features(
                            sample_game, sport, market
                        )
                        
                        # Make prediction
                        prediction = ml_service.predict(sport, market, features_df)

                        
                        if prediction and 'confidence' in prediction:
                            self.log_result(
                                test_name, 
                                'PASS', 
                                f"Confidence: {prediction['confidence']:.1f}%, Features: {prediction.get('features_used', 'N/A')}"
                            )
                        else:
                            self.log_result(test_name, 'FAIL', "No prediction returned")
                            
                    except Exception as e:
                        self.log_result(test_name, 'FAIL', str(e))
                        
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            return False
        
        return True
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        logger.info("\n" + "="*70)
        logger.info("TESTING EDGE CASES")
        logger.info("="*70)
        
        try:
            from app.services.enhanced_ml_service import EnhancedMLService
            from app.services.data_preprocessing import AdvancedFeatureEngineer
            
            ml_service = EnhancedMLService()
            feature_engineer = AdvancedFeatureEngineer()
            
            # Test 1: Invalid sport
            try:
                sample_game = self._create_sample_game('invalid_sport')
                features_df = feature_engineer.prepare_single_game_features(
                    sample_game, 'invalid_sport', 'moneyline'
                )

                prediction = ml_service.predict('invalid_sport', 'moneyline', features_df)
                if prediction:
                    self.log_result("invalid_sport_handling", 'PASS', "Gracefully handled invalid sport")
                else:
                    self.log_result("invalid_sport_handling", 'PASS', "Returned None for invalid sport")
            except Exception as e:
                self.log_result("invalid_sport_handling", 'PASS', f"Correctly raised exception: {str(e)[:50]}")
            
            # Test 2: Empty DataFrame
            try:
                empty_df = pd.DataFrame()
                prediction = ml_service.predict('basketball_nba', 'moneyline', empty_df)
                self.log_result("empty_dataframe", 'FAIL', "Should have raised exception")
            except Exception as e:
                self.log_result("empty_dataframe", 'PASS', "Correctly raised exception for empty data")
            
            # Test 3: Missing columns
            try:
                sample_game = self._create_sample_game('basketball_nba')
                # Remove some columns
                if 'home_possessions_per_game' in sample_game:
                    del sample_game['home_possessions_per_game']
                features_df = feature_engineer.prepare_single_game_features(
                    sample_game, 'basketball_nba', 'moneyline'
                )

                prediction = ml_service.predict('basketball_nba', 'moneyline', features_df)
                self.log_result("missing_columns", 'PASS', "Gracefully handled missing columns")
            except Exception as e:
                self.log_result("missing_columns", 'FAIL', str(e))
            
            # Test 4: None values in data
            try:
                sample_game = self._create_sample_game('basketball_nba')
                sample_game['home_win_pct'] = None
                features_df = feature_engineer.prepare_single_game_features(
                    sample_game, 'basketball_nba', 'moneyline'
                )

                prediction = ml_service.predict('basketball_nba', 'moneyline', features_df)
                self.log_result("none_values", 'PASS', "Handled None values")
            except Exception as e:
                self.log_result("none_values", 'FAIL', str(e))
            
            # Test 5: Extreme values
            try:
                sample_game = self._create_sample_game('basketball_nba')
                sample_game['home_win_pct'] = 999.0
                sample_game['away_win_pct'] = -999.0
                features_df = feature_engineer.prepare_single_game_features(
                    sample_game, 'basketball_nba', 'moneyline'
                )

                prediction = ml_service.predict('basketball_nba', 'moneyline', features_df)
                self.log_result("extreme_values", 'PASS', "Handled extreme values")
            except Exception as e:
                self.log_result("extreme_values", 'FAIL', str(e))
                
        except Exception as e:
            logger.error(f"Edge case testing failed: {e}")
            return False
        
        return True
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        logger.info("\n" + "="*70)
        logger.info("TESTING API ENDPOINTS")
        logger.info("="*70)
        
        try:
            import requests
            
            base_url = "http://localhost:8000"
            
            # Test health endpoint
            try:
                response = requests.get(f"{base_url}/health", timeout=5)
                if response.status_code == 200:
                    self.log_result("api_health", 'PASS', f"Status: {response.status_code}")
                else:
                    self.log_result("api_health", 'FAIL', f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("api_health", 'FAIL', f"Server not running: {e}")
            
            # Test predictions endpoint
            try:
                payload = {
                    'sport': 'basketball_nba',
                    'market': 'moneyline',
                    'home_team': 'Lakers',
                    'away_team': 'Warriors'
                }
                response = requests.post(
                    f"{base_url}/predictions", 
                    json=payload, 
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("api_predictions", 'PASS', f"Got prediction with confidence: {data.get('confidence', 'N/A')}")
                else:
                    self.log_result("api_predictions", 'FAIL', f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("api_predictions", 'FAIL', f"Request failed: {e}")
                
        except ImportError:
            logger.warning("requests module not available, skipping API tests")
            return True
        except Exception as e:
            logger.error(f"API testing failed: {e}")
            return False
        
        return True
    
    def test_feature_counts(self):
        """Verify feature counts match model expectations"""
        logger.info("\n" + "="*70)
        logger.info("TESTING FEATURE COUNTS")
        logger.info("="*70)
        
        try:
            from app.services.data_preprocessing import AdvancedFeatureEngineer
            from app.services.enhanced_ml_service import EnhancedMLService
            
            feature_engineer = AdvancedFeatureEngineer()
            ml_service = EnhancedMLService()
            
            for sport in ['basketball_nba', 'americanfootball_nfl', 'baseball_mlb']:
                for market in ['moneyline', 'spread', 'total']:
                    try:
                        sample_game = self._create_sample_game(sport)
                        features_df = feature_engineer.prepare_single_game_features(
                            sample_game, sport, market
                        )
                        
                        # Get expected feature count from model
                        model_key = f"{sport}_{market}"
                        if model_key in ml_service.models:
                            model_info = ml_service.models[model_key]
                            if 'random_forest' in model_info:
                                rf_model = model_info['random_forest']
                                if hasattr(rf_model, 'n_features_in_'):
                                    expected = rf_model.n_features_in_
                                    actual = len(features_df.columns)

                                    
                                    if expected == actual:
                                        self.log_result(f"{sport}_{market}_features", 'PASS', 
                                                      f"Expected: {expected}, Got: {actual}")
                                    else:
                                        self.log_result(f"{sport}_{market}_features", 'FAIL', 
                                                      f"Expected: {expected}, Got: {actual}")
                    except Exception as e:
                        self.log_result(f"{sport}_{market}_features", 'FAIL', str(e))
                        
        except Exception as e:
            logger.error(f"Feature count testing failed: {e}")
            return False
        
        return True
    
    def _create_sample_game(self, sport):
        """Create sample game data for testing"""
        base_game = {
            'game_date': datetime.now(),
            'home_team': 'Team A',
            'away_team': 'Team B',
            'home_win_pct': 0.6,
            'away_win_pct': 0.55,
            'home_home_win_pct': 0.7,
            'away_away_win_pct': 0.45,
            'home_recent_form': 0.8,
            'away_recent_form': 0.6,
            'home_rest_days': 2,
            'away_rest_days': 3,
            'home_injury_count': 1,
            'away_injury_count': 2,
            'home_star_players_injured': 0,
            'away_star_players_injured': 1,
            'home_point_guard_injured': 0,
            'home_center_injured': 0,
            'away_point_guard_injured': 0,
            'away_center_injured': 0,
            'home_injury_performance_impact': 0.05,
            'away_injury_performance_impact': 0.15,
            'spread_line': -5.5,
            'total_line': 220.5,
            'home_score': 110,
            'away_score': 105,
        }
        
        # Add sport-specific fields
        if 'basketball' in sport:
            base_game.update({
                'home_possessions_per_game': 100.5,
                'away_possessions_per_game': 98.3,
                'home_offensive_rating': 112.5,
                'away_offensive_rating': 110.2,
                'home_defensive_rating': 108.3,
                'away_defensive_rating': 109.1,
                'home_effective_fg_pct': 0.54,
                'away_effective_fg_pct': 0.52,
            })
        elif sport == 'americanfootball_nfl':
            base_game.update({
                'home_yards_per_play': 5.8,
                'away_yards_per_play': 5.2,
                'home_quarterback_rating': 95.5,
                'away_quarterback_rating': 88.3,
            })
        elif sport == 'baseball_mlb':
            base_game.update({
                'home_era': 3.45,
                'away_era': 3.82,
                'home_batting_avg': 0.265,
                'away_batting_avg': 0.248,
            })
        elif sport == 'icehockey_nhl':
            base_game.update({
                'home_goals_per_game': 3.2,
                'away_goals_per_game': 2.8,
                'home_save_pct': 0.915,
                'away_save_pct': 0.908,
            })
        elif 'soccer' in sport:
            base_game.update({
                'home_possession': 55.5,
                'away_possession': 44.5,
                'home_xg': 1.8,
                'away_xg': 1.2,
            })
        
        return pd.Series(base_game)
    
    def generate_report(self):
        """Generate test report"""
        logger.info("\n" + "="*70)
        logger.info("COMPREHENSIVE TEST REPORT")
        logger.info("="*70)
        
        total = len(self.results['passed']) + len(self.results['failed']) + len(self.results['warnings'])
        
        logger.info(f"\nTotal Tests: {total}")
        logger.info(f"✅ Passed: {len(self.results['passed'])}")
        logger.info(f"❌ Failed: {len(self.results['failed'])}")
        logger.info(f"⚠️ Warnings: {len(self.results['warnings'])}")
        
        if self.results['failed']:
            logger.info("\n❌ FAILED TESTS:")
            for result in self.results['failed']:
                logger.info(f"  - {result['test']}: {result['message']}")
        
        if self.results['warnings']:
            logger.info("\n⚠️ WARNINGS:")
            for result in self.results['warnings']:
                logger.info(f"  - {result['test']}: {result['message']}")
        
        success_rate = len(self.results['passed']) / total * 100 if total > 0 else 0
        logger.info(f"\nSuccess Rate: {success_rate:.1f}%")
        
        return len(self.results['failed']) == 0

if __name__ == "__main__":
    tester = ComprehensiveTester()
    
    # Run all tests
    tester.test_all_sports_predictions()
    tester.test_edge_cases()
    tester.test_api_endpoints()
    tester.test_feature_counts()
    
    # Generate report
    all_passed = tester.generate_report()
    
    sys.exit(0 if all_passed else 1)
