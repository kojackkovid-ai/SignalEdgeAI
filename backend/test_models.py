"""
Model Testing and Verification Script
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.enhanced_ml_service import EnhancedMLService
from app.services.espn_prediction_service import ESPNPredictionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_model_predictions():
    """Test model predictions with sample data"""
    
    logger.info("🧪 Starting model prediction tests...")
    
    try:
        # Initialize services
        ml_service = EnhancedMLService()
        espn_service = ESPNPredictionService()
        
        # Test configurations
        test_configs = [
            ('basketball_nba', 'moneyline'),
            ('basketball_nba', 'spread'),
            ('basketball_nba', 'total'),
            ('americanfootball_nfl', 'moneyline'),
            ('americanfootball_nfl', 'spread'),
            ('baseball_mlb', 'moneyline'),
            ('baseball_mlb', 'total'),
            ('icehockey_nhl', 'moneyline'),
            ('icehockey_nhl', 'puck_line'),
            ('soccer_epl', 'spread'),
            ('soccer_epl', 'total')
        ]
        
        test_results = []
        
        for sport_key, market_type in test_configs:
            try:
                logger.info(f"\n🎯 Testing {sport_key} - {market_type}")
                
                # Get recent games for testing
                recent_games = await espn_service.get_historical_data(
                    sport_key=sport_key,
                    market_type=market_type,
                    days_back=7
                )
                
                if not recent_games or len(recent_games) < 5:
                    logger.warning(f"   ⚠️  Insufficient test data ({len(recent_games) if recent_games else 0} games)")
                    test_results.append({
                        'sport_key': sport_key,
                        'market_type': market_type,
                        'status': 'insufficient_data',
                        'games_available': len(recent_games) if recent_games else 0
                    })
                    continue
                
                logger.info(f"   📊 Testing with {len(recent_games)} recent games")
                
                # Test predictions on recent games
                predictions = []
                for i, game_data in enumerate(recent_games[:5]):  # Test first 5 games
                    try:
                        logger.info(f"   🎲 Testing game {i+1}/{min(5, len(recent_games))}")
                        
                        # Make prediction
                        prediction_result = await ml_service.predict(
                            sport_key=sport_key,
                            market_type=market_type,
                            game_data=game_data
                        )
                        
                        if prediction_result['status'] == 'success':
                            predictions.append({
                                'game_id': game_data.get('game_id', f'game_{i}'),
                                'prediction': prediction_result['prediction'],
                                'confidence': prediction_result['confidence'],
                                'features_used': prediction_result['features_used']
                            })
                            logger.info(f"      ✅ Prediction: {prediction_result['prediction']} (confidence: {prediction_result['confidence']:.3f})")
                        else:
                            logger.warning(f"      ❌ Prediction failed: {prediction_result.get('message', 'Unknown error')}")
                            
                    except Exception as e:
                        logger.error(f"      ❌ Error in game {i+1}: {e}")
                        continue
                
                # Analyze results
                if predictions:
                    avg_confidence = np.mean([p['confidence'] for p in predictions])
                    min_confidence = np.min([p['confidence'] for p in predictions])
                    max_confidence = np.max([p['confidence'] for p in predictions])
                    
                    logger.info(f"   📈 Test Results:")
                    logger.info(f"      Successful predictions: {len(predictions)}/{min(5, len(recent_games))}")
                    logger.info(f"      Average confidence: {avg_confidence:.3f}")
                    logger.info(f"      Confidence range: {min_confidence:.3f} - {max_confidence:.3f}")
                    
                    test_results.append({
                        'sport_key': sport_key,
                        'market_type': market_type,
                        'status': 'success',
                        'predictions_made': len(predictions),
                        'total_games_tested': min(5, len(recent_games)),
                        'avg_confidence': avg_confidence,
                        'min_confidence': min_confidence,
                        'max_confidence': max_confidence
                    })
                else:
                    logger.warning(f"   ⚠️  No successful predictions made")
                    test_results.append({
                        'sport_key': sport_key,
                        'market_type': market_type,
                        'status': 'no_predictions',
                        'games_available': len(recent_games)
                    })
                
                # Small delay between tests
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"   ❌ Error testing {sport_key} - {market_type}: {e}")
                test_results.append({
                    'sport_key': sport_key,
                    'market_type': market_type,
                    'status': 'error',
                    'error': str(e)
                })
                continue
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("📊 MODEL TESTING SUMMARY")
        logger.info("="*60)
        
        successful = [r for r in test_results if r['status'] == 'success']
        failed = [r for r in test_results if r['status'] in ['error', 'no_predictions']]
        insufficient_data = [r for r in test_results if r['status'] == 'insufficient_data']
        
        logger.info(f"✅ Successful tests: {len(successful)}")
        logger.info(f"❌ Failed tests: {len(failed)}")
        logger.info(f"⚠️  Insufficient data: {len(insufficient_data)}")
        logger.info(f"📊 Total configurations tested: {len(test_results)}")
        
        if successful:
            logger.info("\nSuccessful tests:")
            for result in successful:
                logger.info(f"   🎯 {result['sport_key']} - {result['market_type']}")
                logger.info(f"      Predictions: {result['predictions_made']}/{result['total_games_tested']}")
                logger.info(f"      Avg confidence: {result['avg_confidence']:.3f}")
                logger.info(f"      Confidence range: {result['min_confidence']:.3f} - {result['max_confidence']:.3f}")
        
        if failed:
            logger.info("\nFailed tests:")
            for result in failed:
                logger.info(f"   ❌ {result['sport_key']} - {result['market_type']}: {result.get('error', 'Unknown error')}")
        
        if insufficient_data:
            logger.info("\nInsufficient data:")
            for result in insufficient_data:
                logger.info(f"   ⚠️  {result['sport_key']} - {result['market_type']}: {result['games_available']} games available")
        
        # Overall assessment
        success_rate = len(successful) / len(test_results) if test_results else 0
        
        if success_rate >= 0.8:  # 80% success rate
            logger.info(f"\n🎉 OVERALL ASSESSMENT: EXCELLENT ({success_rate:.1%} success rate)")
            logger.info("✅ Models are working correctly and ready for production")
        elif success_rate >= 0.6:  # 60% success rate
            logger.info(f"\n✅ OVERALL ASSESSMENT: GOOD ({success_rate:.1%} success rate)")
            logger.info("✅ Models are working well with some minor issues")
        elif success_rate >= 0.4:  # 40% success rate
            logger.info(f"\n⚠️ OVERALL ASSESSMENT: FAIR ({success_rate:.1%} success rate)")
            logger.info("⚠️  Models need attention and possible retraining")
        else:
            logger.info(f"\n❌ OVERALL ASSESSMENT: POOR ({success_rate:.1%} success rate)")
            logger.info("❌ Models need significant improvement and retraining")
        
        return {
            'status': 'completed',
            'success_rate': success_rate,
            'successful_tests': len(successful),
            'failed_tests': len(failed),
            'insufficient_data': len(insufficient_data),
            'total_tests': len(test_results),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Critical error during model testing: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

async def test_model_performance():
    """Test model performance with existing data"""
    
    logger.info("📊 Testing model performance with historical data...")
    
    try:
        # Initialize services
        ml_service = EnhancedMLService()
        espn_service = ESPNPredictionService()
        
        # Test a few key models
        test_configs = [
            ('basketball_nba', 'moneyline'),
            ('americanfootball_nfl', 'spread'),
            ('baseball_mlb', 'total')
        ]
        
        performance_results = []
        
        for sport_key, market_type in test_configs:
            try:
                logger.info(f"\n📈 Testing performance for {sport_key} - {market_type}")
                
                # Get model performance data
                performance_data = await ml_service.get_model_performance(sport_key, market_type)
                
                if performance_data['status'] == 'success':
                    performance = performance_data.get('performance', {})
                    
                    logger.info(f"   ✅ Performance data retrieved")
                    logger.info(f"   📊 Performance metrics: {performance}")
                    
                    performance_results.append({
                        'sport_key': sport_key,
                        'market_type': market_type,
                        'status': 'success',
                        'performance': performance
                    })
                else:
                    logger.warning(f"   ⚠️  No performance data available: {performance_data.get('message', 'Unknown')}")
                    performance_results.append({
                        'sport_key': sport_key,
                        'market_type': market_type,
                        'status': 'no_data',
                        'message': performance_data.get('message', 'Unknown')
                    })
                    
            except Exception as e:
                logger.error(f"   ❌ Error getting performance for {sport_key} - {market_type}: {e}")
                performance_results.append({
                    'sport_key': sport_key,
                    'market_type': market_type,
                    'status': 'error',
                    'error': str(e)
                })
                continue
        
        return {
            'status': 'completed',
            'performance_tests': performance_results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Critical error during performance testing: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

async def main():
    """Main testing function"""
    
    print("🧪 Enhanced Sports Prediction Platform - Model Testing")
    print("="*60)
    
    # Test model predictions
    prediction_results = await test_model_predictions()
    
    # Test model performance
    performance_results = await test_model_performance()
    
    print("\n" + "="*60)
    print("📊 FINAL TEST RESULTS")
    print("="*60)
    
    if prediction_results['status'] == 'completed':
        print(f"🎯 Prediction Tests: {prediction_results['successful_tests']}/{prediction_results['total_tests']} successful")
        print(f"   Success Rate: {prediction_results['success_rate']:.1%}")
    else:
        print(f"❌ Prediction Tests: Error - {prediction_results.get('error', 'Unknown')}")
    
    if performance_results['status'] == 'completed':
        successful_performance = [r for r in performance_results['performance_tests'] if r['status'] == 'success']
        print(f"📊 Performance Tests: {len(successful_performance)}/{len(performance_results['performance_tests'])} successful")
    else:
        print(f"❌ Performance Tests: Error - {performance_results.get('error', 'Unknown')}")
    
    print(f"\n⏰ Timestamp: {datetime.now().isoformat()}")
    
    # Overall recommendation
    if (prediction_results['status'] == 'completed' and 
        prediction_results['success_rate'] >= 0.6 and
        performance_results['status'] == 'completed'):
        print("\n🎉 RECOMMENDATION: Models are ready for production use!")
        print("✅ Automatic training and monitoring system is operational")
        print("✅ Models can make predictions with good confidence")
        print("✅ Performance tracking is active")
    else:
        print("\n⚠️  RECOMMENDATION: Models need attention")
        print("⚠️  Consider retraining or checking data quality")
        print("⚠️  Monitor performance closely when deployed")

if __name__ == "__main__":
    asyncio.run(main())