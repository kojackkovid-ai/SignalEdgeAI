"""
Main entry point for unified training scheduler.
Run with: cd app && python ../ml-models/training/__main__.py
         Or from docker: python /app/ml-models/training/__main__.py
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add ml-models directory to path
ml_models_dir = Path(__file__).parent.parent
sys.path.insert(0, str(ml_models_dir))

# Add app directory to path (for importing app.services.*)
# When running in Docker: /app contains both 'app' and 'ml-models' directories
app_dir = ml_models_dir.parent  # Goes from ml-models up to /app
sys.path.insert(0, str(app_dir))

from training.unified_scheduler import UnifiedTrainingScheduler


async def main():
    """Main entry point for the training scheduler"""
    scheduler = UnifiedTrainingScheduler()
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal, stopping scheduler...")
        asyncio.create_task(scheduler.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await scheduler.start()
    except Exception as e:
        logger.error(f"Scheduler encountered an error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
