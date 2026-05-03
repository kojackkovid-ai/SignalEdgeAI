"""
Graceful Shutdown Handler
Handles graceful shutdown of the FastAPI application
"""

import logging
import asyncio
import signal
import sys
from typing import Callable, Optional, List
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class GracefulShutdown:
    """
    Handles graceful shutdown of FastAPI application
    """

    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.cleanup_tasks: List[Callable] = []
        self.logger = logging.getLogger(__name__)

    def add_cleanup_task(self, task: Callable):
        """Add a cleanup task to be executed on shutdown"""
        self.cleanup_tasks.append(task)

    async def shutdown(self):
        """Initiate graceful shutdown"""
        self.logger.info("🛑 Initiating graceful shutdown...")

        # Signal shutdown event
        self.shutdown_event.set()

        # Execute cleanup tasks
        for task in self.cleanup_tasks:
            try:
                if asyncio.iscoroutinefunction(task):
                    await task()
                else:
                    task()
                self.logger.info(f"✅ Cleanup task completed: {task.__name__}")
            except Exception as e:
                self.logger.error(f"❌ Cleanup task failed: {task.__name__} - {e}")

        self.logger.info("✅ Graceful shutdown completed")

    async def wait_for_shutdown(self):
        """Wait for shutdown signal"""
        await self.shutdown_event.wait()

    def is_shutting_down(self) -> bool:
        """Check if shutdown has been initiated"""
        return self.shutdown_event.is_set()


# Global shutdown handler instance
shutdown_handler = GracefulShutdown()

def setup_graceful_shutdown(app):
    """Setup graceful shutdown handlers for the FastAPI app"""

    @app.on_event("startup")
    async def startup_event():
        """Application startup event"""
        logger.info("🚀 Application startup initiated")

        # Setup signal handlers
        def signal_handler(signum, frame):
            logger.info(f"📡 Received signal {signum}, initiating graceful shutdown")
            asyncio.create_task(shutdown_handler.shutdown())

        # Handle common termination signals
        signal.signal(signal.SIGTERM, signal_handler)  # Docker stop
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C

        # Handle Windows signals if applicable
        if sys.platform == "win32":
            signal.signal(signal.SIGBREAK, signal_handler)

        logger.info("✅ Signal handlers configured")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Application shutdown event"""
        logger.info("🔄 Application shutdown event triggered")
        await shutdown_handler.wait_for_shutdown()

    # Add common cleanup tasks
    shutdown_handler.add_cleanup_task(close_database_connections)
    shutdown_handler.add_cleanup_task(close_redis_connections)
    shutdown_handler.add_cleanup_task(stop_background_tasks)

    logger.info("✅ Graceful shutdown configured")


async def close_database_connections():
    """Close database connections gracefully"""
    try:
        from app.database import engine
        if engine:
            await engine.dispose()
            logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database connections: {e}")


async def close_redis_connections():
    """Close Redis connections gracefully"""
    try:
        from app.utils.caching import get_redis_client
        redis_client = get_redis_client()
        if redis_client:
            await redis_client.close()
            logger.info("✅ Redis connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing Redis connections: {e}")


async def stop_background_tasks():
    """Stop background tasks gracefully"""
    try:
        # Cancel any running background tasks
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete with timeout
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("✅ Background tasks stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping background tasks: {e}")


def get_shutdown_handler() -> GracefulShutdown:
    """Get the global shutdown handler instance"""
    return shutdown_handler