"""
Initial Model Training Script
Trains all ML models from scratch using ONLY real ESPN API data
NO synthetic data - NO fake data - ONLY real game outcomes
"""

import asyncio
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import json
from datetime import datetime
import sys
import os
from typing import Dict, Any, List

# Add the project root and ml-models directory to Python path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, 'ml-models'))

# Use ONLY real data collector - NO synthetic data
from training.real_data_collector import RealESPNDataCollector
from training.auto_training import AutoTrainingPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InitialModelTrainer:
    """Handle initial model training with ONLY real ESPN API data"""
    
    def __init__(self):
        # Use ONLY real data collector - NO synthetic data
        self.data_collector = RealESPNDataCollector()
        self.training_pipeline = AutoTrainingPipeline(
            retrain_interval_days=7,
            min_samples=100  # Lower threshold since we use real data
        )
        self.models_path = Path("ml-models/trained")
        self.data_path = Path("ml-models/data")
        
        # Create directories if they don't exist
        self.models_path.mkdir(parents=True, exist_ok=True)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("InitialModelTrainer initialized - using ONLY real ESPN data")
    
    async def train_all_models(self):
        """Train all models with comprehensive REAL ESPN data"""
        logger.info("Starting initial model training with REAL ESPN data...")
        logger.info("NO synthetic data will be used - only real game outcomes")
        
        try:
            # Collect REAL training data from ESPN API
            training_data = await self._collect_real_training_data()
            
            # Train models with each dataset
            results = {}
            
            for sport, data in training_data.items():
                logger.info(f"Training models for {sport}...")
                
                # Train models with sport-specific data
                result = await self.training_pipeline.trigger_retraining(
                    data, 
                    f"Initial training for {sport}"
                )
                
                results[sport] = result
                
                if result['status'] == 'success':
                    logger.info(f"✅ {sport} models trained successfully")
                    # Save sport-specific models
                    await self._save_sport_models(sport, result)
                else:
                    logger.error(f"❌ {sport} training failed: {result.get('error', 'Unknown error')}")
            
            # Train general models with combined data
            logger.info("Training general models with combined data...")
            combined_data = pd.concat(list(training_data.values()), ignore_index=True)
            general_result = await self.training_pipeline.trigger_retraining(
                combined_data,
                "Initial general training with combined sports data"
            )
            
            if general_result['status'] == 'success':
                logger.info("✅ General models trained successfully")
                await self._save_general_models(general_result)
                results['general'] = general_result
            
            # Generate training report
            await self._generate_training_report(results)
            
            logger.info("🎉 Initial model training completed!")
            return results
            
        except Exception as e:
            logger.error(f"Training process failed: {e}")
            raise
    
    async def _collect_real_training_data(self) -> Dict[str, pd.DataFrame]:
        """Collect comprehensive REAL training data from ESPN API"""
        logger.info("Collecting REAL training data from ESPN API...")
        logger.info("NO synthetic data - using only actual game outcomes")
        
        # Fetch 90 days of real historical data
        real_data = await self.data_collector.collect_historical_training_data(
            sport_key=None,  # All sports
            days_back=90
        )
        
        # Verify data quality
        quality_report = await self.data_collector.verify_data_quality(real_data)
        
        if not quality_report['is_pure_real_data']:
            raise RuntimeError("Data quality check failed - synthetic data detected!")
        
        logger.info(f"✅ Verified {len(real_data)} real training records from ESPN API")
        logger.info(f"Sports breakdown: {quality_report['sports_breakdown']}")
        
        # Split by sport for sport-specific training
        training_data = {}
        for sport in real_data['sport_key'].unique():
            sport_df = real_data[real_data['sport_key'] == sport].copy()
            training_data[sport] = sport_df
            
            # Save to CSV for reference
            csv_path = self.data_path / f"{sport}_real_training_data.csv"
            sport_df.to_csv(csv_path, index=False)
            logger.info(f"Saved {len(sport_df)} real {sport} records to {csv_path}")
        
        # Save combined data
        combined_path = self.data_path / "all_sports_real_training_data.csv"
        real_data.to_csv(combined_path, index=False)
        logger.info(f"Saved combined real data ({len(real_data)} records) to {combined_path}")
        
        return training_data
    
    async def _save_sport_models(self, sport: str, training_result: Dict[str, Any]):
        """Save sport-specific trained models"""
        sport_path = self.models_path / sport.lower()
        sport_path.mkdir(exist_ok=True)
        
        # Save individual models
        models = training_result.get('results', {})
        for model_name, result in models.items():
            if result['status'] == 'success':
                model = result['model']
                
                if model_name == 'neural_net':
                    model.save(sport_path / f"{model_name}_model.h5")
                else:
                    import joblib
                    joblib.dump(model, sport_path / f"{model_name}_model.pkl")
        
        # Save weights
        weights = training_result.get('new_weights', {})
        with open(sport_path / "ensemble_weights.json", 'w') as f:
            json.dump(weights, f, indent=2)
        
        # Save evaluation metrics
        evaluations = training_result.get('evaluation_metrics', {})
        with open(sport_path / "evaluation_metrics.json", 'w') as f:
            json.dump(evaluations, f, indent=2, default=str)
        
        logger.info(f"Saved {sport} models to {sport_path}")
    
    async def _save_general_models(self, training_result: Dict[str, Any]):
        """Save general trained models"""
        # Save individual models
        models = training_result.get('results', {})
        for model_name, result in models.items():
            if result['status'] == 'success':
                model = result['model']
                
                if model_name == 'neural_net':
                    model.save(self.models_path / f"{model_name}_model.h5")
                else:
                    import joblib
                    joblib.dump(model, self.models_path / f"{model_name}_model.pkl")
        
        # Save weights
        weights = training_result.get('new_weights', {})
        with open(self.models_path / "ensemble_weights.json", 'w') as f:
            json.dump(weights, f, indent=2)
        
        # Save evaluation metrics
        evaluations = training_result.get('evaluation_metrics', {})
        with open(self.models_path / "evaluation_metrics.json", 'w') as f:
            json.dump(evaluations, f, indent=2, default=str)
        
        logger.info(f"Saved general models to {self.models_path}")
    
    async def _generate_training_report(self, results: Dict[str, Any]):
        """Generate comprehensive training report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'training_summary': {},
            'model_performance': {},
            'recommendations': []
        }
        
        for sport, result in results.items():
            if result['status'] == 'success':
                report['training_summary'][sport] = {
                    'status': 'Success',
                    'samples_used': result.get('samples_used', 0),
                    'training_time': result.get('duration', 0),
                    'models_trained': result.get('models_trained', [])
                }
                
                # Add performance metrics
                evaluations = result.get('evaluation_metrics', {})
                if evaluations:
                    report['model_performance'][sport] = evaluations
            else:
                report['training_summary'][sport] = {
                    'status': 'Failed',
                    'error': result.get('error', 'Unknown error')
                }
        
        # Add recommendations
        report['recommendations'] = [
            "Schedule daily retraining at 2 AM to incorporate new real ESPN data",
            "Monitor model performance and trigger retraining if accuracy drops >2%",
            "Continue using ONLY real ESPN data - never use synthetic data",
            "Implement A/B testing for different model configurations",
            "Add feature importance analysis to identify most predictive factors",
            "Verify daily that training data comes from ESPN API only"
        ]
        
        # Save report
        report_path = self.models_path / "training_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Training report saved to {report_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("🎯 TRAINING SUMMARY")
        print("="*60)
        
        for sport, summary in report['training_summary'].items():
            status_icon = "✅" if summary['status'] == 'Success' else "❌"
            print(f"{status_icon} {sport}: {summary['status']}")
            if summary['status'] == 'Success':
                print(f"   Samples: {summary['samples_used']:,}")
                print(f"   Time: {summary['training_time']:.1f}s")
                print(f"   Models: {', '.join(summary['models_trained'])}")
        
        print(f"\n📊 Report saved to: {report_path}")

async def main():
    """Main training function"""
    trainer = InitialModelTrainer()
    
    print("🚀 Starting initial ML model training with REAL ESPN DATA...")
    print("NO synthetic data will be used - only real game outcomes from ESPN API")
    print("This process may take 15-20 minutes to complete.\n")
    
    try:
        results = await trainer.train_all_models()
        
        print("\n🎉 Training completed successfully!")
        print("Models are now ready for predictions with improved accuracy.")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
