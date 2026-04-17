#!/usr/bin/env python3
"""
Simple Model Retraining Script
Retrains ALL ML models using ONLY real ESPN API data
NO synthetic data - NO mock data - ONLY real game outcomes
"""

import asyncio
import sys
import os
from pathlib import Path
import logging
import json
from datetime import datetime

# Setup paths
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "ml-models"))
sys.path.insert(0, str(ROOT_DIR / "backend"))

# Handle ml-models vs ml_models naming - create __init__.py if needed
ml_models_dir = ROOT_DIR / "ml-models"
init_file = ml_models_dir / "__init__.py"
if not init_file.exists():
    init_file.touch()

# Also check if there's a ml_models directory
ml_models_alt = ROOT_DIR / "ml_models"
if ml_models_alt.exists():
    sys.path.insert(0, str(ml_models_alt))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main retraining function"""
    print("=" * 80)
    print("SPORTS PREDICTION MODEL RETRAINING")
    print("Using ONLY Real ESPN API Data")
    print("NO Synthetic Data - NO Mock Data - NO Random Generation")
    print("=" * 80)
    print()
    
    # Track results
    results = {
        'start_time': datetime.now().isoformat(),
        'sports_trained': [],
        'errors': [],
        'data_summary': {}
    }
    
    try:
        # Step 1: Import required modules
        logger.info("[1/4] Importing modules...")
        
        from ml_models.training.real_data_collector import RealESPNDataCollector
        from app.services.enhanced_ml_service import EnhancedMLService
        
        logger.info("✓ Modules imported successfully")
        
        # Step 2: Collect real training data from ESPN
        logger.info("[2/4] Collecting REAL training data from ESPN API...")
        logger.info("    This will fetch historical game data from ESPN (no synthetic data)")
        
        collector = RealESPNDataCollector()
        
        # Collect 90 days of historical data for all sports
        sports_to_train = [
            "basketball_nba",
            "basketball_ncaa", 
            "icehockey_nhl",
            "americanfootball_nfl",
            "baseball_mlb",
            "soccer_epl",
            "soccer_usa_mls"
        ]
        
        all_training_data = []
        
        for sport in sports_to_train:
            try:
                logger.info(f"    Fetching {sport} data from ESPN...")
                sport_data = await collector.collect_historical_training_data(
                    sport_key=sport,
                    days_back=90
                )
                if sport_data is not None and len(sport_data) > 0:
                    all_training_data.append(sport_data)
                    logger.info(f"    ✓ Got {len(sport_data)} records for {sport}")
                    results['sports_trained'].append(sport)
                else:
                    logger.warning(f"    ⚠ No data found for {sport}")
            except Exception as e:
                logger.error(f"    ❌ Error collecting {sport} data: {e}")
                results['errors'].append(f"{sport}: {str(e)}")
        
        if not all_training_data:
            raise RuntimeError("No training data collected from ESPN API!")
        
        # Combine all data
        import pandas as pd
        combined_data = pd.concat(all_training_data, ignore_index=True)
        
        results['data_summary'] = {
            'total_records': len(combined_data),
            'sports': results['sports_trained'],
            'date_range': {
                'earliest': str(combined_data['game_date'].min()) if 'game_date' in combined_data.columns else 'unknown',
                'latest': str(combined_data['game_date'].max()) if 'game_date' in combined_data.columns else 'unknown'
            }
        }
        
        logger.info(f"✓ Collected {len(combined_data)} total real training records")
        logger.info(f"  Sports: {', '.join(results['sports_trained'])}")
        
        # Step 3: Train models for each sport
        logger.info("[3/4] Training ML models with real ESPN data...")
        
        ml_service = EnhancedMLService()
        
        # Training configurations
        training_configs = [
            # (sport_key, market_type)
            ("basketball_nba", "moneyline"),
            ("basketball_nba", "spread"),
            ("basketball_nba", "total"),
            ("basketball_ncaa", "moneyline"),
            ("basketball_ncaa", "spread"),
            ("icehockey_nhl", "moneyline"),
            ("icehockey_nhl", "puck_line"),
            ("icehockey_nhl", "total"),
            ("americanfootball_nfl", "moneyline"),
            ("americanfootball_nfl", "spread"),
            ("americanfootball_nfl", "total"),
            ("baseball_mlb", "moneyline"),
            ("baseball_mlb", "total"),
            ("soccer_epl", "moneyline"),
            ("soccer_epl", "spread"),
            ("soccer_epl", "total"),
            ("soccer_usa_mls", "moneyline"),
        ]
        
        trained_count = 0
        failed_count = 0
        
        for sport_key, market_type in training_configs:
            try:
                # Filter data for this sport
                sport_data = combined_data[combined_data['sport_key'] == sport_key].copy()
                
                if len(sport_data) < 50:
                    logger.warning(f"    ⚠ Skipping {sport_key} {market_type}: only {len(sport_data)} samples")
                    failed_count += 1
                    continue
                
                logger.info(f"    Training {sport_key} {market_type} ({len(sport_data)} samples)...")
                
                # Convert to list of dicts
                training_records = sport_data.to_dict('records')
                
                # Train the model
                result = await ml_service.train_models(
                    sport_key=sport_key,
                    market_type=market_type,
                    training_data=training_records
                )
                
                if result and result.get('status') == 'success':
                    logger.info(f"    ✓ {sport_key} {market_type} trained successfully")
                    trained_count += 1
                else:
                    logger.error(f"    ❌ {sport_key} {market_type} training failed")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"    ❌ Error training {sport_key} {market_type}: {e}")
                failed_count += 1
        
        # Step 4: Save and report results
        logger.info("[4/4] Saving models and generating report...")
        
        results['trained_count'] = trained_count
        results['failed_count'] = failed_count
        results['end_time'] = datetime.now().isoformat()
        
        # Save report
        report_path = ROOT_DIR / "ml-models" / "logs" / f"retrain_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"✓ Report saved to {report_path}")
        
        # Print summary
        print()
        print("=" * 80)
        print("RETRAINING COMPLETE")
        print("=" * 80)
        print(f"Models Trained: {trained_count}")
        print(f"Models Failed: {failed_count}")
        print(f"Total Training Records: {len(combined_data)}")
        print(f"Sports Trained: {', '.join(results['sports_trained'])}")
        print(f"Data Source: ESPN API ONLY (NO synthetic data)")
        print(f"Report: {report_path}")
        print("=" * 80)
        
        if trained_count > 0:
            print("\n✅ Models successfully retrained with real ESPN data!")
            return True
        else:
            print("\n❌ No models were trained successfully")
            return False
            
    except Exception as e:
        logger.error(f"Critical error during retraining: {e}")
        import traceback
        traceback.print_exc()
        results['errors'].append(str(e))
        
        # Save error report
        report_path = ROOT_DIR / "ml-models" / "logs" / f"retrain_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return False


if __name__ == "__main__":
    # Windows event loop policy
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
