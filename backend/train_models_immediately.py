"""
Immediate Model Training Script
Checks current model status and trains if necessary
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.enhanced_ml_service import EnhancedMLService
from app.services.enhanced_auto_training import EnhancedAutoTrainingPipeline
from app.services.espn_prediction_service import ESPNPredictionService
from app.services.model_monitoring import ModelPerformanceMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def check_and_train_models():
    """Check current model status and train if necessary"""
    
    logger.info("🔍 Starting immediate model training check...")
    
    try:
        # Initialize services
        logger.info("Initializing services...")
        ml_service = EnhancedMLService()
        auto_training = EnhancedAutoTrainingPipeline(
            retrain_interval_days=7,
            min_samples=100,
            performance_threshold=0.05,
            min_accuracy_threshold=0.55
        )
        espn_service = ESPNPredictionService()
        monitor = ModelPerformanceMonitor()
        
        # Check existing models
        models_dir = Path("ml-models/trained")
        existing_models = list(models_dir.glob("*.joblib")) if models_dir.exists() else []
        
        logger.info(f"Found {len(existing_models)} existing model files")
        
        # Define training configurations
        training_configs = [
            ('basketball_nba', 'moneyline'),
            ('basketball_nba', 'spread'),
            ('basketball_nba', 'total'),
            ('americanfootball_nfl', 'moneyline'),
            ('americanfootball_nfl', 'spread'),
            ('americanfootball_nfl', 'total'),
            ('baseball_mlb', 'moneyline'),
            ('baseball_mlb', 'total'),
            ('icehockey_nhl', 'moneyline'),
            ('icehockey_nhl', 'puck_line'),
            ('icehockey_nhl', 'total'),
            ('soccer_epl', 'spread'),
            ('soccer_epl', 'total')
        ]
        
        training_results = []
        
        for sport_key, market_type in training_configs:
            try:
                logger.info(f"\n🎯 Processing {sport_key} - {market_type}")
                
                # Check if model exists and is recent
                model_key = f"{sport_key}_{market_type}"
                model_file = models_dir / f"{model_key}_ensemble.joblib"
                
                if model_file.exists():

                    # Check file age
                    file_age = datetime.now() - datetime.fromtimestamp(model_file.stat().st_mtime)
                    if file_age.days < 7:
                        logger.info(f"   ✅ Model is recent (age: {file_age.days} days) - skipping")
                        continue
                    else:
                        logger.info(f"   ⚠️  Model is outdated (age: {file_age.days} days) - will retrain")
                
                # Fetch training data
                logger.info(f"   📊 Fetching training data...")
                training_data = await espn_service.get_historical_data(
                    sport_key=sport_key,
                    days_back=90  # Get 90 days of data for comprehensive training
                )

                
                if not training_data or len(training_data) < 50:
                    logger.warning(f"   ⚠️  Insufficient training data ({len(training_data) if training_data else 0} games) - skipping")
                    continue
                
                logger.info(f"   📈 Training on {len(training_data)} games")
                
                # Convert to DataFrame
                df = pd.DataFrame(training_data)
                
                # Check data quality
                if df.empty or 'target' not in df.columns:
                    logger.error(f"   ❌ Invalid training data format")
                    continue
                
                # Perform comprehensive training
                logger.info(f"   🚀 Starting comprehensive training...")
                result = await auto_training.comprehensive_check_and_retrain(
                    df, sport_key, market_type
                )
                
                if result['status'] == 'success':
                    logger.info(f"   ✅ Training completed successfully!")
                    logger.info(f"      Duration: {result['duration']:.1f}s")
                    logger.info(f"      Samples used: {result['samples_used']}")
                    logger.info(f"      Models trained: {', '.join(result['models_trained'])}")
                    
                    # Log evaluation metrics
                    eval_results = result.get('evaluation_results', {})
                    if eval_results:
                        for model_name, metrics in eval_results.items():
                            if 'accuracy' in metrics:
                                logger.info(f"      {model_name}: accuracy={metrics['accuracy']:.3f}, f1={metrics.get('f1', 0):.3f}")
                            elif 'mae' in metrics:
                                logger.info(f"      {model_name}: mae={metrics['mae']:.3f}, rmse={metrics.get('rmse', 0):.3f}")
                    
                    training_results.append({
                        'sport_key': sport_key,
                        'market_type': market_type,
                        'status': 'success',
                        'duration': result['duration'],
                        'samples': result['samples_used'],
                        'models': result['models_trained']
                    })
                    
                else:
                    logger.error(f"   ❌ Training failed: {result.get('error', 'Unknown error')}")
                    training_results.append({
                        'sport_key': sport_key,
                        'market_type': market_type,
                        'status': 'failed',
                        'error': result.get('error', 'Unknown error')
                    })
                
                # Small delay between training sessions
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"   ❌ Error training {sport_key} - {market_type}: {e}")
                training_results.append({
                    'sport_key': sport_key,
                    'market_type': market_type,
                    'status': 'error',
                    'error': str(e)
                })
                continue
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("📊 TRAINING SUMMARY")
        logger.info("="*60)
        
        successful = [r for r in training_results if r['status'] == 'success']
        failed = [r for r in training_results if r['status'] in ['failed', 'error']]
        
        logger.info(f"✅ Successfully trained: {len(successful)} models")
        logger.info(f"❌ Failed: {len(failed)} models")
        
        if successful:
            logger.info("\nSuccessful trainings:")
            for result in successful:
                logger.info(f"   🎯 {result['sport_key']} - {result['market_type']}")
                logger.info(f"      Duration: {result['duration']:.1f}s, Samples: {result['samples']}")
        
        if failed:
            logger.info("\nFailed trainings:")
            for result in failed:
                logger.info(f"   ❌ {result['sport_key']} - {result['market_type']}: {result.get('error', 'Unknown error')}")
        
        # Performance monitoring setup
        logger.info("\n🔍 Setting up performance monitoring...")
        
        # Start monitoring
        await monitor.start_monitoring()
        logger.info("✅ Performance monitoring started")
        
        # Generate initial performance report
        logger.info("\n📈 Initial Performance Report:")
        for sport_key, market_type in [('basketball_nba', 'moneyline'), ('americanfootball_nfl', 'spread')]:
            try:
                summary = await monitor.get_performance_summary(sport_key=sport_key, market_type=market_type, days_back=7)
                if 'overall_accuracy' in summary:
                    logger.info(f"   {sport_key} - {market_type}: {summary['overall_accuracy']:.2%} accuracy")
                else:
                    logger.info(f"   {sport_key} - {market_type}: No performance data yet")
            except Exception as e:
                logger.warning(f"   {sport_key} - {market_type}: Could not get performance data - {e}")
        
        logger.info("\n🎉 Immediate model training completed!")
        logger.info("📅 Automatic retraining is scheduled to run every 24 hours")
        logger.info("🔔 Performance monitoring is active and will alert on issues")
        
        return {
            'status': 'completed',
            'successful_trainings': len(successful),
            'failed_trainings': len(failed),
            'total_models': len(training_results),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Critical error during immediate training: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

async def main():
    """Main function"""
    print("🏀⚽🏈🎾 Enhanced Sports Prediction Platform - Immediate Model Training")
    print("="*70)
    
    result = await check_and_train_models()
    
    print("\n" + "="*70)
    print("Training session completed!")
    print(f"Status: {result['status']}")
    
    if result['status'] == 'completed':
        print(f"Successful trainings: {result['successful_trainings']}")
        print(f"Failed trainings: {result['failed_trainings']}")
        print(f"Total models processed: {result['total_models']}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    print(f"Timestamp: {result['timestamp']}")

if __name__ == "__main__":
    # Run the immediate training
    asyncio.run(main())
