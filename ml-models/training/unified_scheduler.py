"""
Unified Training Scheduler
Consolidates all training scheduler functionality into a single, robust implementation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class UnifiedTrainingScheduler:
    """
    Unified scheduler for ML model training with support for:
    - Daily scheduled training
    - On-demand training
    - Performance-based retraining triggers
    - Multiple sport/market combinations
    """
    
    def __init__(
        self,
        retrain_interval_hours: int = 24,
        min_samples: int = 50,
        performance_threshold: float = 0.05,
        min_accuracy_threshold: float = 0.55,
        max_retries: int = 3
    ):
        self.retrain_interval = timedelta(hours=retrain_interval_hours)
        self.min_samples = min_samples
        self.performance_threshold = performance_threshold
        self.min_accuracy_threshold = min_accuracy_threshold
        self.max_retries = max_retries
        
        # State tracking
        self.last_training: Optional[datetime] = None
        self.training_history: List[Dict[str, Any]] = []
        self.is_running = False
        self._stop_event = asyncio.Event()
        
        # Training configuration
        self.training_configs = [
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
        
        # Status file for persistence
        self.status_file = Path("training_status.json")
        self._load_status()
    
    def _load_status(self):
        """Load training status from file"""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    status = json.load(f)
                    self.last_training = datetime.fromisoformat(status.get('last_training')) if status.get('last_training') else None
                    self.training_history = status.get('history', [])
            except Exception as e:
                logger.warning(f"Could not load training status: {e}")
    
    def _save_status(self):
        """Save training status to file"""
        try:
            status = {
                'last_training': self.last_training.isoformat() if self.last_training else None,
                'history': self.training_history[-100:]  # Keep last 100 records
            }
            with open(self.status_file, 'w') as f:
                json.dump(status, f, default=str)
        except Exception as e:
            logger.warning(f"Could not save training status: {e}")
    
    async def start(self):
        """Start the training scheduler loop"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self._stop_event.clear()
        logger.info("🚀 Starting unified training scheduler")
        
        try:
            while not self._stop_event.is_set():
                await self._run_training_cycle()
                
                # Wait for next cycle or until stopped
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self.retrain_interval.total_seconds()
                    )
                except asyncio.TimeoutError:
                    pass  # Normal timeout, continue to next cycle
        
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        finally:
            self.is_running = False
            logger.info("🛑 Training scheduler stopped")
    
    async def stop(self):
        """Stop the training scheduler"""
        logger.info("Stopping training scheduler...")
        self._stop_event.set()
    
    async def _run_training_cycle(self):
        """Execute one training cycle"""
        logger.info("📊 Starting training cycle")
        start_time = datetime.utcnow()
        
        results = []
        for sport_key, market_type in self.training_configs:
            if self._stop_event.is_set():
                break
            
            result = await self._train_single_model(sport_key, market_type)
            results.append(result)
            
            # Small delay between models to prevent resource exhaustion
            await asyncio.sleep(1)
        
        # Update status
        self.last_training = start_time
        self._save_status()
        
        # Log summary
        successful = sum(1 for r in results if r.get('status') == 'success')
        logger.info(f"✅ Training cycle complete: {successful}/{len(results)} models trained successfully")
    
    async def _train_single_model(self, sport_key: str, market_type: str, retry_count: int = 0) -> Dict[str, Any]:
        """Train a single model with retry logic"""
        try:
            logger.info(f"Training {sport_key} - {market_type}")
            
            # Import here to avoid circular dependencies
            from app.services.espn_prediction_service import ESPNPredictionService
            from app.services.enhanced_ml_service import EnhancedMLService
            
            espn_service = ESPNPredictionService()
            ml_service = EnhancedMLService()
            
            # Fetch training data
            training_data = await espn_service.get_historical_data(
                sport_key=sport_key,
                days_back=14
            )
            
            if not training_data or len(training_data) < self.min_samples:
                return {
                    'status': 'skipped',
                    'sport_key': sport_key,
                    'market_type': market_type,
                    'reason': f'Insufficient data ({len(training_data) if training_data else 0} samples)'
                }
            
            # Train model
            import pandas as pd
            df = pd.DataFrame(training_data)
            
            result = await ml_service.train_models(sport_key, market_type, df.to_dict('records'))
            
            if result.get('status') == 'success':
                logger.info(f"✅ Successfully trained {sport_key} - {market_type}")
                return {
                    'status': 'success',
                    'sport_key': sport_key,
                    'market_type': market_type,
                    'samples': len(training_data)
                }
            else:
                raise Exception(result.get('message', 'Training failed'))
        
        except Exception as e:
            logger.error(f"❌ Error training {sport_key} - {market_type}: {e}")
            
            # Retry logic
            if retry_count < self.max_retries:
                logger.info(f"Retrying {sport_key} - {market_type} (attempt {retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(5 * (retry_count + 1))  # Exponential backoff
                return await self._train_single_model(sport_key, market_type, retry_count + 1)
            
            return {
                'status': 'failed',
                'sport_key': sport_key,
                'market_type': market_type,
                'error': str(e)
            }
    
    async def trigger_manual_training(self, sport_key: Optional[str] = None, market_type: Optional[str] = None) -> Dict[str, Any]:
        """Trigger manual training for specific or all models"""
        if sport_key and market_type:
            return await self._train_single_model(sport_key, market_type)
        
        # Train all configured models
        results = []
        for sk, mt in self.training_configs:
            if sport_key and sk != sport_key:
                continue
            
            result = await self._train_single_model(sk, mt)
            results.append(result)
        
        return {
            'status': 'complete',
            'results': results,
            'successful': sum(1 for r in results if r.get('status') == 'success'),
            'failed': sum(1 for r in results if r.get('status') == 'failed')
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            'is_running': self.is_running,
            'last_training': self.last_training.isoformat() if self.last_training else None,
            'next_training': (self.last_training + self.retrain_interval).isoformat() if self.last_training else None,
            'training_configs': self.training_configs,
            'history_count': len(self.training_history)
        }
