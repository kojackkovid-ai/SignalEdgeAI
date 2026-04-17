#!/usr/bin/env python3
"""
Comprehensive Model Training Script - FIXED VERSION
Trains ML models for all sports and markets with proper error handling
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.enhanced_ml_service import EnhancedMLService
from app.services.data_preprocessing import AdvancedFeatureEngineer

# Configure logging - use ASCII-only to avoid Windows console issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('training_fixed.log')
    ]
)
logger = logging.getLogger(__name__)

# Training configurations for all sports
TRAINING_CONFIGS = [
    # NBA
    ('basketball_nba', 'moneyline'),
    ('basketball_nba', 'spread'),
    ('basketball_nba', 'total'),
    # NFL
    ('americanfootball_nfl', 'moneyline'),
    ('americanfootball_nfl', 'spread'),
    ('americanfootball_nfl', 'total'),
    # MLB
    ('baseball_mlb', 'moneyline'),
    ('baseball_mlb', 'total'),
    # NHL
    ('icehockey_nhl', 'moneyline'),
    ('icehockey_nhl', 'puck_line'),
    ('icehockey_nhl', 'total'),
    # Soccer leagues
    ('soccer_epl', 'moneyline'),
    ('soccer_epl', 'spread'),
    ('soccer_epl', 'total'),
    ('soccer_usa_mls', 'moneyline'),
    ('soccer_usa_mls', 'spread'),
    ('soccer_usa_mls', 'total'),
    ('soccer_esp.1', 'moneyline'),
    ('soccer_esp.1', 'spread'),
    ('soccer_esp.1', 'total'),
    ('soccer_ita.1', 'moneyline'),
    ('soccer_ita.1', 'spread'),
    ('soccer_ita.1', 'total'),
    ('soccer_ger.1', 'moneyline'),
    ('soccer_ger.1', 'spread'),
    ('soccer_ger.1', 'total'),
    ('soccer_fra.1', 'moneyline'),
    ('soccer_fra.1', 'spread'),
    ('soccer_fra.1', 'total'),
]

def generate_synthetic_training_data(sport_key, market_type, n_samples=500):
    """
    Generate synthetic training data for a sport/market combination
    """
    np.random.seed(42)
    data = []
    
    for i in range(n_samples):
        # Base stats
        home_wins = np.random.randint(5, 30)
        home_losses = np.random.randint(5, 30)
        away_wins = np.random.randint(5, 30)
        away_losses = np.random.randint(5, 30)
        
        home_win_pct = home_wins / (home_wins + home_losses)
        away_win_pct = away_wins / (away_wins + away_losses)
        
        # Generate scores based on win percentages (better teams score more)
        home_score = np.random.poisson(100 + (home_win_pct - 0.5) * 20)
        away_score = np.random.poisson(100 + (away_win_pct - 0.5) * 20)
        
        # Add some randomness
        home_score += np.random.randint(-15, 15)
        away_score += np.random.randint(-15, 15)
        
        row = {
            'home_wins': home_wins,
            'home_losses': home_losses,
            'away_wins': away_wins,
            'away_losses': away_losses,
            'home_recent_wins': np.random.randint(0, 5),
            'away_recent_wins': np.random.randint(0, 5),
            'home_points_for': np.random.randint(90, 120),
            'home_points_against': np.random.randint(90, 120),
            'away_points_for': np.random.randint(90, 120),
            'away_points_against': np.random.randint(90, 120),
            'home_opponent_win_pct': np.random.uniform(0.3, 0.7),
            'away_opponent_win_pct': np.random.uniform(0.3, 0.7),
            'game_date': pd.Timestamp('2024-01-01'),
            'home_last_game_date': pd.Timestamp('2023-12-30'),
            'away_last_game_date': pd.Timestamp('2023-12-29'),
            'home_score': home_score,
            'away_score': away_score,
            'spread_line': np.random.uniform(-10, 10),
            'total_line': np.random.uniform(200, 230),
            # Add sport-specific features
            'home_goals_for': np.random.randint(20, 40),
            'home_goals_against': np.random.randint(20, 40),
            'away_goals_for': np.random.randint(20, 40),
            'away_goals_against': np.random.randint(20, 40),
            'home_matches_played': np.random.randint(10, 40),
            'away_matches_played': np.random.randint(10, 40),
        }
        data.append(row)
    
    return data

async def train_single_model(ml_service, sport_key, market_type):
    """
    Train a single model for a sport/market combination
    """
    try:
        logger.info(f"Training {sport_key} - {market_type}")
        
        # Generate synthetic training data
        training_data = generate_synthetic_training_data(sport_key, market_type)
        logger.info(f"  Generated {len(training_data)} training samples")
        
        # Train the model
        result = await ml_service.train_models(sport_key, market_type, training_data)
        
        if result and result.get('status') == 'success':
            logger.info(f"  SUCCESS: Trained {len(result.get('models', []))} models")
            return {
                'sport_key': sport_key,
                'market_type': market_type,
                'status': 'success',
                'models': result.get('models', [])
            }
        else:
            error_msg = result.get('error', 'Unknown error') if result else 'No result'
            logger.error(f"  FAILED: {error_msg}")
            return {
                'sport_key': sport_key,
                'market_type': market_type,
                'status': 'failed',
                'error': error_msg
            }
            
    except Exception as e:
        logger.error(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            'sport_key': sport_key,
            'market_type': market_type,
            'status': 'error',
            'error': str(e)
        }

async def main():
    """
    Main training function
    """
    logger.info("=" * 70)
    logger.info("COMPREHENSIVE MODEL TRAINING - FIXED VERSION")
    logger.info("=" * 70)
    
    # Initialize ML service
    ml_service = EnhancedMLService()
    
    results = []
    successful = 0
    failed = 0
    
    # Train all models
    for sport_key, market_type in TRAINING_CONFIGS:
        result = await train_single_model(ml_service, sport_key, market_type)
        results.append(result)
        
        if result['status'] == 'success':
            successful += 1
        else:
            failed += 1
        
        # Small delay between trainings
        await asyncio.sleep(1)
    
    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("TRAINING SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total configurations: {len(TRAINING_CONFIGS)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success rate: {successful / len(TRAINING_CONFIGS) * 100:.1f}%")
    
    # List failed trainings
    if failed > 0:
        logger.info("")
        logger.info("Failed trainings:")
        for result in results:
            if result['status'] != 'success':
                logger.info(f"  - {result['sport_key']} {result['market_type']}: {result.get('error', 'Unknown')}")
    
    logger.info("")
    logger.info("Training complete!")
    
    return {
        'total': len(TRAINING_CONFIGS),
        'successful': successful,
        'failed': failed,
        'results': results
    }

if __name__ == "__main__":
    # Run the training
    result = asyncio.run(main())
    
    # Exit with appropriate code
    sys.exit(0 if result['failed'] == 0 else 1)
