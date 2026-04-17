"""
ML System Setup and Initialization Script
Sets up the complete ML training and prediction system
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MLSystemSetup:
    """Complete ML system setup and initialization"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.ml_models_path = self.project_root / "ml-models"
        self.backend_path = self.project_root / "backend"
        
    def check_dependencies(self):
        """Check and install required dependencies"""
        logger.info("🔍 Checking dependencies...")
        
        required_packages = [
            'pandas', 'numpy', 'scikit-learn', 'xgboost', 'lightgbm',
            'tensorflow', 'joblib', 'schedule'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                logger.info(f"✅ {package} is installed")
            except ImportError:
                missing_packages.append(package)
                logger.warning(f"❌ {package} is missing")
        
        if missing_packages:
            logger.info(f"Installing missing packages: {', '.join(missing_packages)}")
            try:
                # Try installing packages one by one to avoid total failure
                for package in missing_packages:
                    try:
                        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                        logger.info(f"✅ {package} installed successfully")
                    except subprocess.CalledProcessError as e:
                        if package == 'tensorflow':
                            logger.warning(f"⚠️ Failed to install tensorflow (likely due to path length). Continuing without it.")
                            logger.warning(f"   Neural Network model will be disabled.")
                        else:
                            logger.error(f"❌ Failed to install {package}: {e}")
                            return False
            except Exception as e:
                logger.error(f"❌ Unexpected error during installation: {e}")
                return False
        
        return True
    
    def create_directory_structure(self):
        """Create necessary directory structure"""
        logger.info("📁 Creating directory structure...")
        
        directories = [
            self.ml_models_path / "trained",
            self.ml_models_path / "data",
            self.ml_models_path / "logs",
            self.ml_models_path / "training",
            self.ml_models_path / "reasoning",
            self.ml_models_path / "models"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created directory: {directory}")
        
        return True
    
    async def run_initial_training(self):
        """Run initial model training"""
        logger.info("🎯 Starting initial model training...")
        
        try:
            # Change to the correct directory
            os.chdir(self.project_root)
            
            # Import and run the training script
            sys.path.append(str(self.project_root))
            sys.path.append(str(self.ml_models_path))
            
            from training.initial_training import InitialModelTrainer
            
            trainer = InitialModelTrainer()
            results = await trainer.train_all_models()
            
            logger.info("✅ Initial training completed successfully!")
            return results
            
        except Exception as e:
            logger.error(f"❌ Initial training failed: {e}")
            return None
    
    def create_systemd_service(self):
        """Create systemd service for daily training (Linux) or Windows Task Scheduler (Windows)"""
        import platform
        
        system = platform.system()
        
        if system == "Windows":
            self._create_windows_task_scheduler()
        elif system == "Linux":
            self._create_systemd_service()
        else:
            logger.warning(f"⚠️  Automatic scheduler setup not supported for {system}")
            logger.warning("Please set up manual cron job or scheduled task")
    
    def _create_windows_task_scheduler(self):
        """Create Windows Task Scheduler job for daily training"""
        logger.info("🪟 Setting up Windows Task Scheduler...")
        
        # Create PowerShell script to run the daily scheduler
        ps_script = f"""
# Daily ML Training Task
$action = New-ScheduledTaskAction -Execute "{sys.executable}" -Argument "{self.ml_models_path / 'training' / 'daily_scheduler_new.py'}" -WorkingDirectory "{self.project_root}"
$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Description "Daily ML Model Training at 2 AM"
Register-ScheduledTask -TaskName "ML-DailyTraining" -InputObject $task -Force
"""
        
        ps_script_path = self.ml_models_path / "setup_ml_task.ps1"
        with open(ps_script_path, 'w') as f:
            f.write(ps_script)
        
        logger.info(f"✅ PowerShell script created: {ps_script_path}")
        logger.info("To set up the scheduled task, run this command as Administrator:")
        logger.info(f"PowerShell -ExecutionPolicy Bypass -File \"{ps_script_path}\"")
    
    def _create_systemd_service(self):
        """Create systemd service for daily training (Linux)"""
        logger.info("🐧 Setting up systemd service...")
        
        service_content = f"""[Unit]
Description=ML Model Daily Training
After=network.target

[Service]
Type=oneshot
User={os.getenv('USER')}
WorkingDirectory={self.project_root}
ExecStart={sys.executable} {self.ml_models_path / 'training' / 'daily_scheduler_new.py'}
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        
        timer_content = f"""[Unit]
Description=Run ML Training Daily at 2 AM
Requires=ml-training.service

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
"""
        
        service_path = self.ml_models_path / "ml-training.service"
        timer_path = self.ml_models_path / "ml-training.timer"
        
        with open(service_path, 'w') as f:
            f.write(service_content)
        
        with open(timer_path, 'w') as f:
            f.write(timer_content)
        
        logger.info(f"✅ Systemd files created:")
        logger.info(f"   Service: {service_path}")
        logger.info(f"   Timer: {timer_path}")
        logger.info("To install the service, run:")
        logger.info(f"sudo cp {service_path} /etc/systemd/system/")
        logger.info(f"sudo cp {timer_path} /etc/systemd/system/")
        logger.info("sudo systemctl daemon-reload")
        logger.info("sudo systemctl enable ml-training.timer")
        logger.info("sudo systemctl start ml-training.timer")
    
    def create_startup_script(self):
        """Create startup script for easy system initialization"""
        logger.info("📝 Creating startup script...")
        
        startup_script = f"""#!/bin/bash
# ML System Startup Script
# Run this script to start the ML training system

echo "🚀 Starting ML System..."

# Change to project directory
cd {self.project_root}

# Run the daily scheduler in the background
echo "📅 Starting daily training scheduler..."
python {self.ml_models_path / 'training' / 'daily_scheduler_new.py'} &

SCHEDULER_PID=$!
echo "✅ Daily training scheduler started with PID: $SCHEDULER_PID"
echo "📝 Scheduler logs will be saved to: {self.ml_models_path / 'logs'}"
echo ""
echo "🎯 To stop the scheduler, run: kill $SCHEDULER_PID"
echo "📊 To check status, run: ps aux | grep daily_scheduler"
"""
        
        startup_path = self.ml_models_path / "start_ml_system.sh"
        with open(startup_path, 'w') as f:
            f.write(startup_script)
        
        # Make executable on Unix systems
        try:
            os.chmod(startup_path, 0o755)
        except:
            pass
        
        logger.info(f"✅ Startup script created: {startup_path}")
    
    def create_configuration_file(self):
        """Create configuration file for ML system"""
        logger.info("⚙️  Creating configuration file...")
        
        config = {
            "ml_system": {
                "version": "1.0.0",
                "last_updated": datetime.now().isoformat(),
                "training_schedule": "daily at 2:00 AM",
                "models": {
                    "xgboost": {"enabled": True, "weight": 0.35},
                    "lightgbm": {"enabled": True, "weight": 0.30},
                    "neural_net": {"enabled": True, "weight": 0.25},
                    "linear": {"enabled": True, "weight": 0.10}
                },
                "training_parameters": {
                    "min_samples": 100,
                    "retrain_interval_days": 1,
                    "confidence_threshold": 0.55,
                    "max_confidence": 0.95
                },
                "data_sources": {
                    "synthetic_data": True,
                    "historical_data": False,
                    "real_time_data": False
                }
            },
            "logging": {
                "level": "INFO",
                "file_rotation": True,
                "max_log_files": 30
            },
            "notifications": {
                "enabled": False,
                "webhook_url": "",
                "email_recipients": []
            }
        }
        
        config_path = self.ml_models_path / "config.json"
        import json
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"✅ Configuration file created: {config_path}")
    
    async def setup_complete_system(self):
        """Run complete system setup"""
        logger.info("🚀 Starting complete ML system setup...")
        logger.info("=" * 60)
        
        # Step 1: Check dependencies
        if not self.check_dependencies():
            logger.error("❌ Dependency check failed")
            return False
        
        # Step 2: Create directory structure
        if not self.create_directory_structure():
            logger.error("❌ Directory creation failed")
            return False
        
        # Step 3: Run initial training
        logger.info("\n🎯 Step 3: Running initial model training...")
        logger.info("This will take 10-15 minutes to complete...")
        training_results = await self.run_initial_training()
        
        if not training_results:
            logger.error("❌ Initial training failed")
            return False
        
        # Step 4: Create configuration
        self.create_configuration_file()
        
        # Step 5: Create startup script
        self.create_startup_script()
        
        # Step 6: Create scheduled task/service
        self.create_systemd_service()
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 ML System Setup Complete!")
        logger.info("=" * 60)
        
        self.print_setup_summary(training_results)
        
        return True
    
    def print_setup_summary(self, training_results):
        """Print setup summary and next steps"""
        print("\n📋 SETUP SUMMARY:")
        print("-" * 40)
        
        for sport, result in training_results.items():
            if result.get('status') == 'success':
                print(f"✅ {sport}: Models trained successfully")
                print(f"   📊 Samples: {result.get('samples_used', 0):,}")
                print(f"   ⏱️  Duration: {result.get('duration', 0):.1f}s")
            else:
                print(f"❌ {sport}: Training failed")
        
        print(f"\n📁 System locations:")
        print(f"   📍 Project root: {self.project_root}")
        print(f"   🧠 ML models: {self.ml_models_path / 'trained'}")
        print(f"   📊 Training data: {self.ml_models_path / 'data'}")
        print(f"   📝 Logs: {self.ml_models_path / 'logs'}")
        
        print(f"\n🚀 Next steps:")
        print(f"   1. Start the system: bash {self.ml_models_path / 'start_ml_system.sh'}")
        print(f"   2. Monitor logs: tail -f {self.ml_models_path / 'logs' / 'daily_training.log'}")
        print(f"   3. Check training history: cat {self.ml_models_path / 'logs' / 'training_history.json'}")
        
        print(f"\n⏰ Daily training will run automatically at 2:00 AM")
        print(f"📊 Models will be retrained with fresh data every day")
        print(f"🔔 Check logs for training status and performance metrics")

async def main():
    """Main setup function"""
    setup = MLSystemSetup()
    
    try:
        success = await setup.setup_complete_system()
        
        if success:
            print("\n🎉 Setup completed successfully!")
            print("Your ML prediction system is ready to use.")
        else:
            print("\n❌ Setup failed. Check logs for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())