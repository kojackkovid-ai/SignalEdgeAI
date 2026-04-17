"""
Comprehensive Model Retraining Script
Retrains ALL models using ONLY real ESPN API data - NO synthetic data allowed
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, List

# Get the ml-models directory as base (this file is in ml-models/training/)
ML_MODELS_DIR = Path(__file__).parent.resolve()  # ml-models/training
PROJECT_ROOT = ML_MODELS_DIR.parent.resolve()    # ml-models

# Create logs directory first
logs_dir = PROJECT_ROOT / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

# Setup logging with absolute path
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(str(logs_dir / 'retrain_real_data.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add paths
backend_dir = PROJECT_ROOT / "backend"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(PROJECT_ROOT))

# Import real data collector
from training.real_data_collector import RealESPNDataCollector

# Import ML service
EnhancedMLService: Any = None
HAS_ML_SERVICE: bool = False

try:
    from app.services.enhanced_ml_service import EnhancedMLService  # type: ignore
    HAS_ML_SERVICE = True
except ImportError:
    logger.error("Cannot import EnhancedMLService - ML training unavailable")


class RealDataModelRetrainer:
    """
    Retrains all ML models using ONLY real ESPN API data.
    NO synthetic data, NO mock data, NO random generation.
    """
    
    def __init__(self):
        self.data_collector = RealESPNDataCollector()
        self.ml_service = EnhancedMLService() if (HAS_ML_SERVICE and EnhancedMLService is not None) else None

        
        # Paths - use absolute paths based on PROJECT_ROOT
        self.models_dir = PROJECT_ROOT / "trained"
        self.logs_dir = PROJECT_ROOT / "logs"
        self.data_dir = PROJECT_ROOT / "data"
        
        # Create directories
        for path in [self.models_dir, self.logs_dir, self.data_dir]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Sports and markets to train
        self.training_configs = [
            # NBA
            ("basketball_nba", "moneyline"),
            ("basketball_nba", "spread"),
            ("basketball_nba", "total"),
            # NCAAB
            ("basketball_ncaa", "moneyline"),
            ("basketball_ncaa", "spread"),
            # NHL
            ("icehockey_nhl", "moneyline"),
            ("icehockey_nhl", "puck_line"),
            ("icehockey_nhl", "total"),
            # NFL
            ("americanfootball_nfl", "moneyline"),
            ("americanfootball_nfl", "spread"),
            ("americanfootball_nfl", "total"),
            # MLB
            ("baseball_mlb", "moneyline"),
            ("baseball_mlb", "total"),
            # Soccer
            ("soccer_epl", "moneyline"),
            ("soccer_epl", "spread"),
            ("soccer_usa_mls", "moneyline"),
            ("soccer_esp.1", "moneyline"),
            ("soccer_ita.1", "moneyline"),
            ("soccer_ger.1", "moneyline"),
            ("soccer_fra.1", "moneyline"),
        ]
        
        logger.info("=" * 70)
        logger.info("REAL DATA MODEL RETRAINER INITIALIZED")
        logger.info("Using ONLY real ESPN API data - NO synthetic data")
        logger.info("=" * 70)
    
    async def retrain_all_models(self, days_back: int = 90) -> Dict[str, Any]:
        """
        Retrain all models with real ESPN data.
        
        Args:
            days_back: Number of days of historical data to use (default 90)
            
        Returns:
            Training results summary
        """
        start_time = datetime.now()
        logger.info(f"\n{'='*70}")
        logger.info(f"STARTING FULL MODEL RETRAINING WITH REAL DATA")
        logger.info(f"Date: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Historical data: {days_back} days")
        logger.info(f"{'='*70}\n")
        
        results = {
            "start_time": start_time.isoformat(),
            "days_back": days_back,
            "models_trained": [],
            "models_failed": [],
            "data_summary": {},
            "training_summary": {}
        }
        
        try:
            # Step 1: Collect real training data
            logger.info("STEP 1: Collecting real training data from ESPN API...")
            training_data = await self._collect_real_training_data(days_back)
            
            if training_data is None or len(training_data) == 0:
                raise RuntimeError("No real training data collected - cannot proceed")
            
            results["data_summary"] = {
                "total_records": len(training_data),
                "sports_breakdown": training_data['sport_key'].value_counts().to_dict(),
                "date_range": {
                    "earliest": training_data['game_date'].min(),
                    "latest": training_data['game_date'].max()
                }
            }
            
            # Save training data for reference
            data_file = self.data_dir / f"real_training_data_{start_time.strftime('%Y%m%d_%H%M%S')}.csv"
            training_data.to_csv(data_file, index=False)
            logger.info(f"Saved training data to {data_file}")
            
            # Step 2: Train models for each sport/market
            logger.info(f"\nSTEP 2: Training models for {len(self.training_configs)} sport/market combinations...")
            
            for sport_key, market_type in self.training_configs:
                try:
                    result = await self._train_single_model(
                        sport_key, 
                        market_type, 
                        training_data
                    )
                    
                    if result and result.get('status') == 'success':
                        results["models_trained"].append({
                            "sport_key": sport_key,
                            "market_type": market_type,
                            "accuracy": result.get('accuracy', 0),
                            "samples": result.get('samples', 0)
                        })
                        logger.info(f"✅ Successfully trained {sport_key} {market_type}")
                    else:
                        error_msg = result.get('error', 'Unknown error') if result else 'No result'
                        results["models_failed"].append({
                            "sport_key": sport_key,
                            "market_type": market_type,
                            "error": error_msg
                        })
                        logger.error(f"❌ Failed to train {sport_key} {market_type}: {error_msg}")
                        
                except Exception as e:
                    results["models_failed"].append({
                        "sport_key": sport_key,
                        "market_type": market_type,
                        "error": str(e)
                    })
                    logger.error(f"❌ Exception training {sport_key} {market_type}: {e}")
            
            # Step 3: Generate final report
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            results["end_time"] = end_time.isoformat()
            results["duration_seconds"] = duration
            results["success_rate"] = len(results["models_trained"]) / len(self.training_configs) if self.training_configs else 0
            
            await self._generate_final_report(results)
            
            logger.info(f"\n{'='*70}")
            logger.info(f"RETRAINING COMPLETE")
            logger.info(f"Duration: {duration:.1f} seconds")
            logger.info(f"Models trained: {len(results['models_trained'])}")
            logger.info(f"Models failed: {len(results['models_failed'])}")
            logger.info(f"Success rate: {results['success_rate']*100:.1f}%")
            logger.info(f"{'='*70}\n")
            
            return results
            
        except Exception as e:
            logger.error(f"Critical error during retraining: {e}")
            results["error"] = str(e)
            return results
    
    async def _collect_real_training_data(self, days_back: int) -> pd.DataFrame:
        """
        Collect real training data from ESPN API.
        """
        logger.info(f"Fetching {days_back} days of real game data from ESPN API...")
        
        try:
            # Use the real data collector
            df = await self.data_collector.collect_historical_training_data(
                sport_key=None,  # All sports
                days_back=days_back
            )
            
            # Verify data quality
            quality_report = await self.data_collector.verify_data_quality(df)
            
            logger.info(f"\nData Quality Verification:")
            logger.info(f"  Total records: {quality_report['total_records']}")
            logger.info(f"  Is pure real data: {quality_report['is_pure_real_data']}")
            logger.info(f"  Data source check: {quality_report['data_source_check']}")
            logger.info(f"  Real outcomes: {quality_report['real_outcomes']}")
            logger.info(f"  Sports breakdown: {quality_report['sports_breakdown']}")
            
            if not quality_report['is_pure_real_data']:
                raise RuntimeError("Data quality check failed - synthetic data detected!")
            
            return df
            
        except Exception as e:
            logger.error(f"Error collecting real training data: {e}")
            raise
    
    async def _train_single_model(
        self, 
        sport_key: str, 
        market_type: str, 
        training_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Train a single model for specific sport and market.
        """
        if not self.ml_service:
            return {"status": "error", "error": "ML service not available"}
        
        try:
            # Filter data for this sport
            sport_data = training_data[training_data['sport_key'] == sport_key].copy()
            
            if len(sport_data) < 50:
                logger.warning(f"Insufficient data for {sport_key}: {len(sport_data)} records")
                return {"status": "error", "error": f"Insufficient data: {len(sport_data)} records"}
            
            logger.info(f"Training {sport_key} {market_type} with {len(sport_data)} real records...")
            
            # Convert to list of dicts for ML service
            training_records = sport_data.to_dict('records')
            
            # Train the model
            result = await self.ml_service.train_models(
                sport_key=sport_key,
                market_type=market_type,
                training_data=training_records,
                historical_data=None  # Not using historical param
            )
            
            # Extract accuracy if available
            accuracy = 0
            if result and 'model_scores' in result:
                scores = result['model_scores']
                if scores:
                    first_model = list(scores.values())[0]
                    accuracy = first_model.get('accuracy', 0)
            
            return {
                "status": "success" if result and result.get('status') == 'success' else "error",
                "accuracy": accuracy,
                "samples": len(sport_data),
                "full_result": result
            }
            
        except Exception as e:
            logger.error(f"Error training {sport_key} {market_type}: {e}")
            return {"status": "error", "error": str(e)}
    
    def _verify_no_synthetic_data(self, df: pd.DataFrame) -> bool:
        """
        Verify that DataFrame contains no synthetic data.
        Returns True if synthetic data detected (should fail), False if clean.
        """
        # Check data source
        if 'data_source' in df.columns:
            non_espn = df[df['data_source'] != 'espn_api_real']
            if len(non_espn) > 0:
                logger.error(f"Synthetic data detected: {len(non_espn)} records with non-ESPN data source")
                return True
        
        # Check for synthetic indicators
        synthetic_indicators = ['synthetic', 'fake', 'mock', 'simulated', 'random', 'generated']
        
        for col in df.columns:
            if df[col].dtype == 'object':
                for indicator in synthetic_indicators:
                    if df[col].str.contains(indicator, case=False, na=False).any():
                        logger.error(f"Synthetic data detected: Found '{indicator}' in column {col}")
                        return True
        
        # Check for suspicious patterns
        for col in df.select_dtypes(include=[np.number]).columns:
            if df[col].nunique() == 1 and len(df) > 10:
                logger.error(f"Synthetic data detected: Column {col} has all identical values")
                return True
        
        logger.info("✅ Data verification passed - no synthetic data detected")
        return False

    async def _generate_final_report(self, results: Dict[str, Any]):
        """
        Generate comprehensive training report.
        """

        report_file = self.logs_dir / f"retrain_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Add summary statistics
        report = {
            "report_type": "REAL_DATA_RETRAINING",
            "timestamp": datetime.now().isoformat(),
            "data_source": "ESPN_API_ONLY",
            "synthetic_data_used": False,
            "summary": {
                "total_models_attempted": len(self.training_configs),
                "models_trained_successfully": len(results["models_trained"]),
                "models_failed": len(results["models_failed"]),
                "success_rate": results.get("success_rate", 0),
                "duration_seconds": results.get("duration_seconds", 0)
            },
            "data_summary": results.get("data_summary", {}),
            "successful_models": results["models_trained"],
            "failed_models": results["models_failed"]
        }
        
        # Save report
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Training report saved to {report_file}")
        
        # Print summary
        print("\n" + "="*70)
        print("RETRAINING SUMMARY")
        print("="*70)
        print(f"Data Source: ESPN API ONLY (NO synthetic data)")
        print(f"Total Models: {report['summary']['total_models_attempted']}")
        print(f"Successful: {report['summary']['models_trained_successfully']}")
        print(f"Failed: {report['summary']['models_failed']}")
        print(f"Success Rate: {report['summary']['success_rate']*100:.1f}%")
        print(f"Duration: {report['summary']['duration_seconds']:.1f} seconds")
        print("="*70)
        
        if results["models_trained"]:
            print("\nSuccessfully Trained Models:")
            for model in results["models_trained"]:
                print(f"  ✅ {model['sport_key']} - {model['market_type']} "
                      f"(Accuracy: {model.get('accuracy', 0):.3f}, "
                      f"Samples: {model.get('samples', 0)})")
        
        if results["models_failed"]:
            print("\nFailed Models:")
            for model in results["models_failed"]:
                print(f"  ❌ {model['sport_key']} - {model['market_type']}: "
                      f"{model.get('error', 'Unknown error')}")
        
        print("="*70)


async def main():
    """
    Main entry point for retraining all models with real data.
    """
    print("\n" + "="*70)
    print("SPORTS PREDICTION MODEL RETRAINING")
    print("Using ONLY Real ESPN API Data")
    print("NO Synthetic Data - NO Mock Data - NO Random Generation")
    print("="*70 + "\n")
    
    # Get days back from environment or use default
    days_back = int(os.environ.get('TRAINING_DAYS_BACK', '90'))
    
    print(f"Configuration:")
    print(f"  Historical data: {days_back} days")
    print(f"  Data source: ESPN API ONLY")
    print(f"  Synthetic data: DISABLED")
    print()
    
    # Confirm before proceeding
    confirm = input("Proceed with retraining? (yes/no): ").lower().strip()
    if confirm not in ['yes', 'y']:
        print("Retraining cancelled.")
        return
    
    # Run retraining
    retrainer = RealDataModelRetrainer()
    results = await retrainer.retrain_all_models(days_back=days_back)
    
    # Final status
    success_rate = results.get('success_rate', 0)
    if success_rate >= 0.8:
        print(f"\n🎉 Retraining completed successfully! ({success_rate*100:.1f}% success rate)")
    elif success_rate >= 0.5:
        print(f"\n⚠️ Retraining completed with partial success ({success_rate*100:.1f}% success rate)")
    else:
        print(f"\n❌ Retraining completed with many failures ({success_rate*100:.1f}% success rate)")
    
    print(f"\nLog file: ml-models/logs/retrain_real_data.log")
    print(f"Report saved to: ml-models/logs/retrain_report_*.json")


if __name__ == "__main__":
    # Windows event loop policy
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())
