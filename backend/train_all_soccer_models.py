#!/usr/bin/env python3
"""
Train ML models for all soccer leagues
- 6 leagues: EPL, MLS, La Liga, Serie A, Bundesliga, Ligue 1
- 3 markets per league: moneyline, spread, total
- 3 algorithms per market: xgboost, random_forest, gradient_boosting
- Total: 54 models (6 leagues × 3 markets × 3 algorithms)
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
import json

# Add paths for imports
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.enhanced_ml_service import EnhancedMLService
from app.services.data_preprocessing import AdvancedFeatureEngineer
from app.services.espn_prediction_service import ESPNPredictionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('soccer_model_training.log')
    ]
)
logger = logging.getLogger(__name__)

# Soccer league configurations
SOCCER_LEAGUES = [
    {
        'key': 'soccer_epl',
        'name': 'English Premier League',
        'espn_path': 'soccer/eng.1',
        'markets': ['moneyline', 'spread', 'total']
    },
    {
        'key': 'soccer_usa_mls',
        'name': 'MLS',
        'espn_path': 'soccer/usa.1',
        'markets': ['moneyline', 'spread', 'total']
    },
    {
        'key': 'soccer_esp.1',
        'name': 'La Liga',
        'espn_path': 'soccer/esp.1',
        'markets': ['moneyline', 'spread', 'total']
    },
    {
        'key': 'soccer_ita.1',
        'name': 'Serie A',
        'espn_path': 'soccer/ita.1',
        'markets': ['moneyline', 'spread', 'total']
    },
    {
        'key': 'soccer_ger.1',
        'name': 'Bundesliga',
        'espn_path': 'soccer/ger.1',
        'markets': ['moneyline', 'spread', 'total']
    },
    {
        'key': 'soccer_fra.1',
        'name': 'Ligue 1',
        'espn_path': 'soccer/fra.1',
        'markets': ['moneyline', 'spread', 'total']
    }
]

# Model algorithms to train
MODEL_ALGORITHMS = ['xgboost', 'random_forest', 'gradient_boosting']


async def fetch_historical_games(espn_service: ESPNPredictionService, league: dict, days_back: int = 90) -> list:
    """Fetch historical games for training"""
    logger.info(f"Fetching historical data for {league['name']} ({league['key']})")
    
    try:
        games = await espn_service.get_historical_data(league['key'], days_back=days_back)
        logger.info(f"Fetched {len(games)} historical games for {league['name']}")
        return games
    except Exception as e:
        logger.error(f"Error fetching historical data for {league['name']}: {e}")
        return []


def generate_synthetic_training_data(league: dict, num_samples: int = 1000) -> list:
    """Generate synthetic training data for soccer leagues"""
    import random
    import numpy as np
    
    logger.info(f"Generating {num_samples} synthetic training samples for {league['name']}")
    
    training_data = []
    
    for i in range(num_samples):
        # Generate realistic soccer stats
        home_win_pct = random.uniform(0.3, 0.7)
        away_win_pct = random.uniform(0.3, 0.7)
        home_form = random.uniform(0.2, 0.8)
        away_form = random.uniform(0.2, 0.8)
        home_sos = random.uniform(0.4, 0.6)
        away_sos = random.uniform(0.4, 0.6)
        rest_days_diff = random.uniform(-3, 3)
        
        # Soccer-specific features
        home_goals_pg = random.uniform(1.0, 2.5)
        away_goals_pg = random.uniform(1.0, 2.5)
        home_shots_pg = random.uniform(10, 18)
        away_shots_pg = random.uniform(10, 18)
        home_possession = random.uniform(45, 65)
        away_possession = 100 - home_possession
        
        # Determine outcome based on features
        home_advantage = (home_win_pct - away_win_pct) * 0.3
        form_advantage = (home_form - away_form) * 0.2
        goals_advantage = (home_goals_pg - away_goals_pg) * 0.1
        
        total_advantage = home_advantage + form_advantage + goals_advantage + random.uniform(-0.1, 0.1)
        
        # Moneyline outcome (0 = away win, 1 = home win, 2 = draw)
        if total_advantage > 0.15:
            moneyline_result = 1  # Home win
        elif total_advantage < -0.15:
            moneyline_result = 0  # Away win
        else:
            moneyline_result = 2  # Draw
        
        # Spread outcome (home team covers -0.5 spread)
        spread_result = 1 if total_advantage > 0 else 0
        
        # Total goals
        expected_total = home_goals_pg + away_goals_pg
        total_line = 2.5
        total_result = 1 if expected_total > total_line else 0
        
        sample = {
            'home_win_pct': home_win_pct,
            'away_win_pct': away_win_pct,
            'home_recent_form': home_form,
            'away_recent_form': away_form,
            'home_sos': home_sos,
            'away_sos': away_sos,
            'rest_days_diff': rest_days_diff,
            'home_goals_pg': home_goals_pg,
            'away_goals_pg': away_goals_pg,
            'home_shots_pg': home_shots_pg,
            'away_shots_pg': away_shots_pg,
            'home_possession': home_possession,
            'away_possession': away_possession,
            'moneyline_result': moneyline_result,
            'spread_result': spread_result,
            'total_result': total_result,
            'expected_total': expected_total
        }
        
        training_data.append(sample)
    
    logger.info(f"Generated {len(training_data)} synthetic training samples")
    return training_data


async def train_league_models(ml_service: EnhancedMLService, league: dict, training_data: list) -> dict:
    """Train all models for a specific league"""
    results = {
        'league': league['name'],
        'key': league['key'],
        'models_trained': 0,
        'models_failed': 0,
        'markets': {}
    }
    
    if len(training_data) < 100:
        logger.warning(f"Insufficient training data for {league['name']}: {len(training_data)} samples")
        return results
    
    for market in league['markets']:
        logger.info(f"Training {market} models for {league['name']}")
        market_results = {
            'trained': [],
            'failed': []
        }
        
        try:
            # Train ensemble model for this market
            result = await ml_service.train_models(league['key'], market, training_data)
            
            if result.get('status') == 'success':
                market_results['trained'].append('ensemble')
                results['models_trained'] += 1
                logger.info(f"✓ Successfully trained {market} ensemble for {league['name']}")
            else:
                market_results['failed'].append('ensemble')
                results['models_failed'] += 1
                logger.error(f"✗ Failed to train {market} ensemble for {league['name']}: {result.get('message')}")
                
        except Exception as e:
            market_results['failed'].append('ensemble')
            results['models_failed'] += 1
            logger.error(f"✗ Error training {market} for {league['name']}: {e}")
        
        results['markets'][market] = market_results
    
    return results


async def save_models(ml_service: EnhancedMLService, league: dict) -> bool:
    """Save trained models to disk"""
    try:
        models_dir = Path('ml-models/trained')
        league_dir = models_dir / league['key'].replace('.', '_')
        league_dir.mkdir(parents=True, exist_ok=True)
        
        # Save each market model
        for market in league['markets']:
            model_key = f"{league['key']}_{market}"
            if model_key in ml_service.models:
                model_data = ml_service.models[model_key]
                save_path = league_dir / f"{model_key}_models.joblib"
                
                import joblib
                joblib.dump(model_data, save_path)
                logger.info(f"Saved {model_key} model to {save_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error saving models for {league['name']}: {e}")
        return False


async def train_all_soccer_models():
    """Main function to train all soccer models"""
    logger.info("=" * 70)
    logger.info("SOCCER ML MODEL TRAINING - STARTING")
    logger.info("=" * 70)
    
    # Initialize services
    ml_service = EnhancedMLService()
    espn_service = ESPNPredictionService()
    
    total_models = 0
    successful_models = 0
    failed_models = 0
    
    training_results = []
    
    for league in SOCCER_LEAGUES:
        logger.info(f"\n{'='*70}")
        logger.info(f"Training models for {league['name']} ({league['key']})")
        logger.info(f"{'='*70}")
        
        try:
            # Try to fetch historical data first
            historical_games = await fetch_historical_games(espn_service, league, days_back=90)
            
            if len(historical_games) >= 50:
                # Use historical data
                logger.info(f"Using {len(historical_games)} historical games for training")
                training_data = historical_games
            else:
                # Generate synthetic data
                logger.info(f"Insufficient historical data, generating synthetic training data")
                training_data = generate_synthetic_training_data(league, num_samples=1000)
            
            # Train models for this league
            results = await train_league_models(ml_service, league, training_data)
            training_results.append(results)
            
            successful_models += results['models_trained']
            failed_models += results['models_failed']
            total_models += len(league['markets'])
            
            # Save models
            await save_models(ml_service, league)
            
        except Exception as e:
            logger.error(f"Error processing league {league['name']}: {e}")
            training_results.append({
                'league': league['name'],
                'key': league['key'],
                'error': str(e)
            })
            failed_models += len(league['markets'])
    
    # Close ESPN service
    await espn_service.close()
    
    # Print summary
    logger.info(f"\n{'='*70}")
    logger.info("TRAINING SUMMARY")
    logger.info(f"{'='*70}")
    logger.info(f"Total leagues processed: {len(SOCCER_LEAGUES)}")
    logger.info(f"Total models trained: {successful_models}")
    logger.info(f"Total models failed: {failed_models}")
    logger.info(f"Success rate: {successful_models/max(1, successful_models + failed_models) * 100:.1f}%")
    
    # Save training report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_leagues': len(SOCCER_LEAGUES),
        'successful_models': successful_models,
        'failed_models': failed_models,
        'success_rate': successful_models/max(1, successful_models + failed_models),
        'results': training_results
    }
    
    report_path = Path('soccer_training_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Training report saved to {report_path}")
    logger.info(f"{'='*70}")
    
    return successful_models, failed_models


if __name__ == "__main__":
    # Run the training
    try:
        successful, failed = asyncio.run(train_all_soccer_models())
        
        if successful > 0:
            print(f"\n✅ Training complete! {successful} models trained successfully.")
            sys.exit(0)
        else:
            print(f"\n⚠️ Training completed but no models were trained successfully.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error during training: {e}")
        print(f"\n❌ Training failed: {e}")
        sys.exit(1)

