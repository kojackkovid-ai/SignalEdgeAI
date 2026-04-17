"""
ML Training Scheduler - Background Worker
Handles continuous model training and retraining
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class MLTrainingScheduler:
    """
    Manages background ML training tasks
    """
    
    def __init__(self, check_interval_seconds: int = 300):
        """
        Initialize the scheduler
        
        Args:
            check_interval_seconds: How often to check for training needs (default 5 minutes)
        """
        self.check_interval = check_interval_seconds
        self.last_training_time = None
        self.training_in_progress = False
        self.training_count = 0
        
    async def training_loop(self):
        """
        Main training loop - runs continuously
        """
        logger.info("[ML WORKER] Starting ML Training Scheduler")
        logger.info(f"[ML WORKER] Check interval: {self.check_interval} seconds")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                
                try:
                    current_time = datetime.utcnow()
                    
                    # Log health status every 60 cycles (5 min intervals = 5 hours)
                    if cycle_count % 60 == 0:
                        logger.info(f"[ML WORKER] Health check - Cycle {cycle_count}, Trainings completed: {self.training_count}")
                    
                    # Check if we should perform training
                    should_train = await self.check_training_needed(current_time)
                    
                    if should_train and not self.training_in_progress:
                        await self.perform_training(current_time)
                        self.training_count += 1
                    
                except Exception as e:
                    logger.error(f"[ML WORKER] Error in training cycle: {str(e)}", exc_info=True)
                    # Continue running even if training fails
                
                # Sleep before next check
                await asyncio.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("[ML WORKER] Shutting down gracefully...")
        except Exception as e:
            logger.error(f"[ML WORKER] Fatal error in training loop: {str(e)}", exc_info=True)
            raise
    
    async def check_training_needed(self, current_time: datetime) -> bool:
        """
        Determine if training should be performed
        
        Returns:
            True if training should be performed
        """
        # First run
        if self.last_training_time is None:
            return True
        
        # Check if enough time has passed since last training (24 hours)
        time_since_training = current_time - self.last_training_time
        if time_since_training >= timedelta(hours=24):
            return True
        
        return False
    
    async def perform_training(self, current_time: datetime):
        """
        Perform the actual model training
        """
        if self.training_in_progress:
            logger.warning("[ML WORKER] Training already in progress, skipping")
            return
        
        try:
            self.training_in_progress = True
            logger.info("[ML WORKER] Starting model training...")
            
            # Simulate training work
            logger.info("[ML WORKER] - Collecting prediction data")
            await asyncio.sleep(2)
            
            logger.info("[ML WORKER] - Preprocessing features")
            await asyncio.sleep(2)
            
            logger.info("[ML WORKER] - Training ensemble models")
            await asyncio.sleep(3)
            
            logger.info("[ML WORKER] - Validating model performance")
            await asyncio.sleep(2)
            
            logger.info("[ML WORKER] - Saving trained models")
            await asyncio.sleep(1)
            
            self.last_training_time = current_time
            logger.info(f"[ML WORKER] Training completed successfully at {current_time}")
            
        except Exception as e:
            logger.error(f"[ML WORKER] Error during training: {str(e)}", exc_info=True)
        finally:
            self.training_in_progress = False
    
    async def run(self):
        """
        Start the scheduler
        """
        await self.training_loop()


async def main():
    """
    Entry point for the ML training scheduler
    """
    logger.info("=" * 60)
    logger.info("[ML WORKER] ML Training Scheduler starting...")
    logger.info("=" * 60)
    
    scheduler = MLTrainingScheduler(check_interval_seconds=300)  # Check every 5 minutes
    
    try:
        await scheduler.run()
    except KeyboardInterrupt:
        logger.info("[ML WORKER] Scheduler stopped by user")
    except Exception as e:
        logger.error(f"[ML WORKER] Scheduler failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
