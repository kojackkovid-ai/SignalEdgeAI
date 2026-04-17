"""
Setup Automatic Training and Monitoring System
"""

import asyncio
import logging
from datetime import datetime
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.enhanced_auto_training import EnhancedAutoTrainingPipeline
from app.services.model_monitoring import ModelPerformanceMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def setup_automatic_system():
    """Setup the automatic training and monitoring system"""
    
    logger.info("🚀 Setting up automatic training and monitoring system...")
    
    try:
        # Create models directory if it doesn't exist
        models_dir = Path("ml-models/trained")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize enhanced auto-training pipeline
        auto_training = EnhancedAutoTrainingPipeline(
            retrain_interval_days=7,  # Retrain every 7 days
            min_samples=100,          # Minimum 100 samples for retraining
            performance_threshold=0.05,  # 5% accuracy drop threshold
            min_accuracy_threshold=0.55   # Minimum 55% accuracy
        )
        
        logger.info("✅ Enhanced auto-training pipeline initialized")
        
        # Initialize model monitoring
        monitor = ModelPerformanceMonitor()
        await monitor.start_monitoring()
        
        logger.info("✅ Model performance monitoring started")
        
        # Test the system with a simple check
        logger.info("🔍 Testing system components...")
        
        # Check training history (should be empty initially)
        history = auto_training.get_training_history()
        logger.info(f"📊 Current training history: {len(history)} sessions")
        
        # Check for any existing alerts
        alerts = await monitor.get_active_alerts()
        logger.info(f"🚨 Active alerts: {len(alerts)}")
        
        # Create a setup completion marker
        setup_marker = models_dir / "auto_training_setup.complete"
        setup_marker.write_text(f"Automatic training system setup completed at {datetime.now().isoformat()}")
        
        logger.info("\n" + "="*60)
        logger.info("🎉 AUTOMATIC TRAINING SYSTEM SETUP COMPLETE!")
        logger.info("="*60)
        logger.info("✅ Enhanced auto-training pipeline is ready")
        logger.info("✅ Model performance monitoring is active")
        logger.info("✅ Automatic retraining will occur every 7 days")
        logger.info("✅ Performance alerts will be generated for:")
        logger.info("   • Accuracy drops below 55%")
        logger.info("   • Accuracy drops by more than 5% from baseline")
        logger.info("   • Poor confidence calibration (ECE > 0.1)")
        logger.info("   • Data drift detection")
        logger.info("✅ Manual retraining can be triggered via API")
        logger.info("\n🔄 The system will automatically:")
        logger.info("   • Monitor model performance in real-time")
        logger.info("   • Retrain models when performance degrades")
        logger.info("   • Alert on performance issues")
        logger.info("   • Track training history and metrics")
        logger.info("   • Clean up old data (keeps 90 days)")
        
        return {
            'status': 'success',
            'message': 'Automatic training system setup complete',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'auto_training': True,
                'monitoring': True,
                'training_history_count': len(history),
                'active_alerts': len(alerts)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error setting up automatic system: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

async def create_training_schedule():
    """Create a training schedule configuration"""
    
    logger.info("📅 Creating training schedule configuration...")
    
    schedule_config = {
        'daily_training_time': '02:00',  # 2 AM UTC
        'retrain_interval_days': 7,
        'min_samples_required': 100,
        'performance_check_interval_hours': 1,
        'data_retention_days': 90,
        'sports_and_markets': [
            {'sport': 'basketball_nba', 'markets': ['moneyline', 'spread', 'total']},
            {'sport': 'americanfootball_nfl', 'markets': ['moneyline', 'spread', 'total']},
            {'sport': 'baseball_mlb', 'markets': ['moneyline', 'total']},
            {'sport': 'icehockey_nhl', 'markets': ['moneyline', 'puck_line', 'total']},
            {'sport': 'soccer_epl', 'markets': ['spread', 'total']}
        ],
        'alert_thresholds': {
            'min_accuracy': 0.55,
            'accuracy_drop_threshold': 0.05,
            'confidence_calibration_threshold': 0.1,
            'data_drift_z_score': 3.0
        }
    }
    
    # Save schedule configuration
    config_path = Path("ml-models/training_schedule.json")
    import json
    with open(config_path, 'w') as f:
        json.dump(schedule_config, f, indent=2)
    
    logger.info(f"✅ Training schedule saved to {config_path}")
    
    return schedule_config

async def main():
    """Main setup function"""
    
    print("🏀⚽🏈🎾 Enhanced Sports Prediction Platform")
    print("="*60)
    print("🔄 Setting up Automatic Training & Monitoring System")
    print("="*60)
    
    # Setup the automatic system
    result = await setup_automatic_system()
    
    if result['status'] == 'success':
        # Create training schedule
        schedule = await create_training_schedule()
        
        print("\n" + "="*60)
        print("🎉 SETUP COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"✅ Status: {result['status']}")
        print(f"✅ Timestamp: {result['timestamp']}")
        print(f"✅ Training history: {result['components']['training_history_count']} sessions")
        print(f"✅ Active alerts: {result['components']['active_alerts']}")
        print(f"✅ Daily training scheduled for: {schedule['daily_training_time']} UTC")
        print(f"✅ Retrain interval: {schedule['retrain_interval_days']} days")
        print(f"✅ Data retention: {schedule['data_retention_days']} days")
        print("\n🔄 The system is now ready for automatic operation!")
        print("🚀 Start the main application to begin automatic training.")
        
    else:
        print(f"\n❌ Setup failed: {result['error']}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)