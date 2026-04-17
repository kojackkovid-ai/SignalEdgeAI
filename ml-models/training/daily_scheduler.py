"""
Daily Training Scheduler
Automated model training every day at 2am with comprehensive data collection
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class DailyTrainingScheduler:
    """
    Schedules and manages daily ML model training at 2am
    """
    
    def __init__(self, training_pipeline, data_collector):
        self.training_pipeline = training_pipeline
        self.data_collector = data_collector
        self.is_running = False
        self.last_training_date = None
        self.training_history = []
        
    async def start_daily_training(self):
        """Start the daily training scheduler"""
        logger.info("Starting daily training scheduler (2am daily)")
        self.is_running = True
        
        while self.is_running:
            try:
                now = datetime.now()
                
                # Check if it's 2am and we haven't trained today
                if now.hour == 2 and now.minute == 0:
                    if self.last_training_date != now.date():
                        logger.info("Triggering daily training at 2am")
                        await self._run_daily_training()
                        self.last_training_date = now.date()
                
                # Wait 1 minute before checking again
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in daily training scheduler: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _run_daily_training(self):
        """Execute daily training with comprehensive data collection"""
        start_time = datetime.now()
        
        try:
            # Step 1: Collect yesterday's game results
            logger.info("Collecting yesterday's game results...")
            yesterday_results = await self.data_collector.collect_yesterday_results()
            
            # Step 2: Collect new training data
            logger.info("Collecting comprehensive training data...")
            training_data = await self.data_collector.collect_training_data()
            
            # Step 3: Validate data quality
            logger.info("Validating training data quality...")
            if not self._validate_training_data(training_data):
                logger.error("Training data validation failed")
                return
            
            # Step 4: Run training pipeline
            logger.info(f"Starting model training with {len(training_data)} samples...")
            training_result = await self.training_pipeline.check_and_retrain(training_data)
            
            # Step 5: Generate training report
            training_report = {
                'timestamp': start_time.isoformat(),
                'data_summary': {
                    'total_samples': len(training_data),
                    'yesterday_games': len(yesterday_results),
                    'data_quality_score': self._calculate_data_quality(training_data)
                },
                'training_result': training_result,
                'duration_minutes': (datetime.now() - start_time).total_seconds() / 60
            }
            
            # Step 6: Save training report
            await self._save_training_report(training_report)
            
            # Step 7: Update model performance tracking
            await self._update_model_performance(training_result)
            
            logger.info(f"Daily training completed successfully in {training_report['duration_minutes']:.1f} minutes")
            
        except Exception as e:
            logger.error(f"Daily training failed: {e}")
            await self._save_error_report(str(e), start_time)
    
    def _validate_training_data(self, data) -> bool:
        """Validate training data quality"""
        if data.empty:
            return False
        
        if len(data) < 500:  # Minimum samples required
            return False
        
        # Check for required columns
        required_columns = ['target', 'home_team_elo', 'away_team_elo', 'home_form', 'away_form']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            logger.warning(f"Missing required columns: {missing_columns}")
        
        # Check data completeness
        completeness = 1 - (data.isnull().sum().sum() / (data.shape[0] * data.shape[1]))
        if completeness < 0.8:  # Less than 80% complete data
            logger.warning(f"Data completeness too low: {completeness:.2%}")
            return False
        
        return True
    
    def _calculate_data_quality(self, data) -> float:
        """Calculate overall data quality score"""
        if data.empty:
            return 0.0
        
        # Completeness score
        completeness = 1 - (data.isnull().sum().sum() / (data.shape[0] * data.shape[1]))
        
        # Sample size score
        sample_size_score = min(len(data) / 1000, 1.0)  # Optimal: 1000+ samples
        
        # Target balance score (for binary classification)
        if 'target' in data.columns:
            target_balance = data['target'].value_counts(normalize=True).min()
            balance_score = 1 - abs(target_balance - 0.5) * 2  # Perfect balance = 1.0
        else:
            balance_score = 0.5
        
        # Overall quality score
        quality_score = (completeness * 0.4 + sample_size_score * 0.3 + balance_score * 0.3)
        
        return round(quality_score, 3)
    
    async def _save_training_report(self, report: Dict[str, Any]):
        """Save training report to file"""
        reports_dir = Path("ml-models/training/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = reports_dir / f"training_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Training report saved: {report_file}")
    
    async def _save_error_report(self, error: str, start_time: datetime):
        """Save error report when training fails"""
        reports_dir = Path("ml-models/training/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        error_report = {
            'timestamp': start_time.isoformat(),
            'error': error,
            'type': 'training_error'
        }
        
        report_file = reports_dir / f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(error_report, f, indent=2, default=str)
        
        logger.error(f"Error report saved: {report_file}")
    
    async def _update_model_performance(self, training_result: Dict[str, Any]):
        """Update model performance tracking"""
        if training_result.get('status') == 'success':
            performance_data = {
                'timestamp': datetime.now().isoformat(),
                'new_weights': training_result.get('new_weights', {}),
                'evaluation_metrics': training_result.get('evaluation_metrics', {}),
                'samples_used': training_result.get('samples_used', 0)
            }
            
            # Save to performance history
            performance_file = Path("ml-models/training/performance_history.json")
            
            # Load existing history
            if performance_file.exists():
                with open(performance_file, 'r') as f:
                    history = json.load(f)
            else:
                history = []
            
            # Add new performance data
            history.append(performance_data)
            
            # Keep only last 100 entries
            history = history[-100:]
            
            # Save updated history
            with open(performance_file, 'w') as f:
                json.dump(history, f, indent=2, default=str)
    
    def stop(self):
        """Stop the daily training scheduler"""
        self.is_running = False
        logger.info("Daily training scheduler stopped")


# Example usage and testing
async def test_daily_training():
    """Test the daily training scheduler"""
    from ml_models.training.auto_training import AutoTrainingPipeline
    from ml_models.training.data_collector import SportsDataCollector
    
    # Initialize components
    training_pipeline = AutoTrainingPipeline(retrain_interval_days=1, min_samples=500)
    data_collector = SportsDataCollector()
    scheduler = DailyTrainingScheduler(training_pipeline, data_collector)
    
    # Run a single training cycle
    print("Testing daily training scheduler...")
    await scheduler._run_daily_training()
    
    print("Daily training test completed!")


if __name__ == "__main__":
    asyncio.run(test_daily_training())