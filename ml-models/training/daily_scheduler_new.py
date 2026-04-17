"""
Automated Daily Training Scheduler
Runs model training daily at 2 AM using ONLY real ESPN API data
NO synthetic data - NO fake data - ONLY real game outcomes
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import pandas as pd
import sys
import os
from pathlib import Path
import json

try:
    import schedule
except ImportError:
    schedule = None
    logging.warning("schedule module not installed - daily scheduling will not work")

# Add the project root and ml-models directory to Python path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, 'ml-models'))

from training.auto_training import AutoTrainingPipeline
# Use ONLY real data collector - NO synthetic data
from training.real_data_collector import RealESPNDataCollector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml-models/logs/daily_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DailyTrainingScheduler:
    """Schedule and manage daily model training with ONLY real ESPN data"""
    
    def __init__(self):
        self.training_pipeline = AutoTrainingPipeline(
            retrain_interval_days=1,  # Force daily retraining
            min_samples=50  # Lower threshold for daily training with real data
        )
        # Use ONLY real data collector - NO synthetic data
        self.data_collector = RealESPNDataCollector()
        self.models_path = Path("ml-models/trained")
        self.data_path = Path("ml-models/data")
        self.logs_path = Path("ml-models/logs")
        
        # Create directories if they don't exist
        for path in [self.models_path, self.data_path, self.logs_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        logger.info("DailyTrainingScheduler initialized - using ONLY real ESPN data")
    
    async def daily_training_job(self):
        """Execute daily training job"""
        logger.info("🚀 Starting daily model training job...")
        start_time = datetime.now()
        
        try:
            # Generate fresh training data for the day
            logger.info("Generating daily training data...")
            daily_data = await self._generate_daily_training_data()
            
            # Train models with new data
            logger.info("Training models with daily data...")
            result = await self.training_pipeline.trigger_retraining(
                daily_data,
                f"Daily scheduled training - {start_time.strftime('%Y-%m-%d')}"
            )
            
            if result['status'] == 'success':
                await self._handle_successful_training(result, start_time)
            else:
                await self._handle_failed_training(result, start_time)
            
            # Generate daily report
            await self._generate_daily_report(result, start_time)
            
            logger.info("✅ Daily training job completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Daily training job failed: {e}")
            await self._send_alert(f"Daily training failed: {e}")
    
    async def _generate_daily_training_data(self) -> pd.DataFrame:
        """Collect REAL training data from ESPN API - NO synthetic data"""
        logger.info("Collecting REAL daily training data from ESPN API...")
        logger.info("NO synthetic data - using only actual completed games")
        
        try:
            # Collect yesterday's real completed games from ESPN API
            real_data = await self.data_collector.collect_daily_training_data()
            
            # Verify data quality
            quality_report = await self.data_collector.verify_data_quality(real_data)
            
            if not quality_report['is_pure_real_data']:
                logger.error("Data quality check failed - synthetic data detected!")
                raise RuntimeError("Synthetic data detected in daily training data")
            
            logger.info(f"✅ Verified {len(real_data)} real training records from ESPN API")
            logger.info(f"Sports breakdown: {quality_report['sports_breakdown']}")
            
            # Save daily training data
            daily_data_file = self.data_path / f"daily_training_real_{datetime.now().strftime('%Y%m%d')}.csv"
            real_data.to_csv(daily_data_file, index=False)
            logger.info(f"Saved real daily training data to {daily_data_file}")
            
            return real_data
            
        except Exception as e:
            logger.error(f"Error collecting real daily training data: {e}")
            raise
    
    async def _handle_successful_training(self, result: Dict[str, Any], start_time: datetime):
        """Handle successful training completion"""
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Training completed successfully in {duration:.1f} seconds")
        logger.info(f"📊 Samples used: {result.get('samples_used', 0):,}")
        logger.info(f"🔧 Models trained: {', '.join(result.get('models_trained', []))}")
        
        # Save updated models
        await self._save_updated_models(result)
        
        # Update training history
        await self._update_training_history(result, start_time, duration, 'success')
    
    async def _handle_failed_training(self, result: Dict[str, Any], start_time: datetime):
        """Handle failed training"""
        duration = (datetime.now() - start_time).total_seconds()
        error_msg = result.get('error', 'Unknown error')
        
        logger.error(f"❌ Training failed after {duration:.1f} seconds: {error_msg}")
        
        # Update training history
        await self._update_training_history(result, start_time, duration, 'failed')
        
        # Send alert (implement based on your notification system)
        await self._send_alert(f"Training failed: {error_msg}")
    
    async def _save_updated_models(self, result: Dict[str, Any]):
        """Save updated models after successful training"""
        models = result.get('results', {})
        weights = result.get('new_weights', {})
        
        # Save each model
        for model_name, model_result in models.items():
            if model_result['status'] == 'success':
                model = model_result['model']
                
                if model_name == 'neural_net':
                    model.save(self.models_path / f"{model_name}_model_latest.h5")
                else:
                    import joblib
                    joblib.dump(model, self.models_path / f"{model_name}_model_latest.pkl")
        
        # Save weights
        if weights:
            with open(self.models_path / "ensemble_weights_latest.json", 'w') as f:
                json.dump(weights, f, indent=2)
        
        logger.info("💾 Updated models saved successfully")
    
    async def _update_training_history(self, result: Dict[str, Any], start_time: datetime, duration: float, status: str):
        """Update training history log"""
        history_file = self.logs_path / "training_history.json"
        
        # Load existing history
        history = []
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []
        
        # Add new entry
        history_entry = {
            'timestamp': start_time.isoformat(),
            'status': status,
            'duration': duration,
            'samples_used': result.get('samples_used', 0),
            'models_trained': result.get('models_trained', []),
            'evaluation_metrics': result.get('evaluation_metrics', {})
        }
        
        history.append(history_entry)
        
        # Keep only last 30 days of history
        if len(history) > 30:
            history = history[-30:]
        
        # Save updated history
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2, default=str)
    
    async def _generate_daily_report(self, result: Dict[str, Any], start_time: datetime):
        """Generate daily training report"""
        report_file = self.logs_path / f"daily_report_{start_time.strftime('%Y%m%d')}.json"
        
        report = {
            'date': start_time.strftime('%Y-%m-%d'),
            'training_status': result.get('status', 'unknown'),
            'duration': (datetime.now() - start_time).total_seconds(),
            'samples_used': result.get('samples_used', 0),
            'models_trained': result.get('models_trained', []),
            'evaluation_metrics': result.get('evaluation_metrics', {}),
            'recommendations': self._generate_recommendations(result)
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📋 Daily report saved to {report_file}")
    
    def _generate_recommendations(self, result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on training results"""
        recommendations = []
        
        if result.get('status') != 'success':
            recommendations.append("Investigate training failure and resolve underlying issues")
            return recommendations
        
        evaluations = result.get('evaluation_metrics', {})
        
        for model_name, metrics in evaluations.items():
            if metrics:
                accuracy = metrics.get('accuracy', 0)
                f1_score = metrics.get('f1', 0)
                
                if accuracy < 0.65:
                    recommendations.append(f"Consider reconfiguring {model_name} - accuracy below 65%")
                
                if f1_score < 0.6:
                    recommendations.append(f"Review {model_name} performance - F1 score below 0.6")
        
        if not recommendations:
            recommendations.append("All models performing well - maintain current configuration")
        
        return recommendations
    
    async def _send_alert(self, message: str):
        """Send alert notification (implement based on your notification system)"""
        logger.warning(f"ALERT: {message}")
        
        # Example: Save alert to file
        alert_file = self.logs_path / f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(alert_file, 'w') as f:
            f.write(f"Alert: {message}\nTime: {datetime.now().isoformat()}")
    
    def schedule_daily_training(self):
        """Schedule daily training at 2 AM"""
        if schedule is None:
            logger.error("schedule module not available - cannot schedule daily training")
            return
            
        schedule.every().day.at("02:00").do(lambda: asyncio.create_task(self.daily_training_job()))
        
        logger.info("📅 Daily training scheduled for 2:00 AM every day")
        
        # Also schedule a test run in 1 minute for immediate testing
        logger.info("🧪 Scheduling test run in 1 minute...")
        schedule.every(1).minutes.do(lambda: asyncio.create_task(self.test_run()))
    
    async def test_run(self):
        """Quick test run to verify system is working with real data"""
        logger.info("🧪 Running system test with REAL ESPN data...")
        
        # Remove the test schedule after first run
        if schedule is not None:
            schedule.clear()
        self.schedule_daily_training()
        
        # Run a quick test with real data
        try:
            # Test real data collection (just 7 days for quick test)
            logger.info("Testing real data collection from ESPN API...")
            test_data = await self.data_collector.collect_historical_training_data(
                sport_key="basketball_nba",
                days_back=7
            )
            logger.info(f"✅ Real data collection successful: {len(test_data)} records")
            
            # Verify data quality
            quality_report = await self.data_collector.verify_data_quality(test_data)
            if quality_report['is_pure_real_data']:
                logger.info("✅ Data quality verified - pure real ESPN data")
            else:
                logger.error("❌ Data quality check failed")
                return
            
            # Test model training with small real dataset
            result = await self.training_pipeline.trigger_retraining(
                test_data,
                "System test run with real data"
            )
            
            if result['status'] == 'success':
                logger.info("✅ System test passed - ready for daily training with real data")
            else:
                logger.error(f"❌ System test failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"❌ System test failed: {e}")
    
    def run_scheduler(self):
        """Run the training scheduler"""
        if schedule is None:
            logger.error("schedule module not available - cannot run scheduler")
            logger.info("Please install schedule: pip install schedule")
            return
            
        logger.info("🚀 Starting Daily Training Scheduler...")
        logger.info("Scheduler will run training every day at 2:00 AM")
        logger.info("Press Ctrl+C to stop\n")
        
        # Initial schedule
        self.schedule_daily_training()
        
        # Run pending tasks
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

async def main():
    """Main function to run the scheduler"""
    scheduler = DailyTrainingScheduler()
    
    # Run initial test
    await scheduler.test_run()
    
    # Start the scheduler
    scheduler.run_scheduler()

if __name__ == "__main__":
    # For Windows, we need to handle the event loop policy
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())
