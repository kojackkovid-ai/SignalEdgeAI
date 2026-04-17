#!/usr/bin/env python3
"""
Simple Model Training Script
Uses existing model infrastructure to retrain all models
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import os
from pathlib import Path
import json

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.enhanced_ml_service import EnhancedMLService
from app.services.data_preprocessing import AdvancedFeatureEngineer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
    # Soccer - EPL
    ('soccer_epl', 'moneyline'),
    ('soccer_epl', 'spread'),
    ('soccer_epl', 'total'),
    # Soccer - MLS
    ('soccer_usa_mls', 'moneyline'),
    ('soccer_usa_mls', 'spread'),
    ('soccer_usa_mls', 'total'),
    # Soccer - La Liga
    ('soccer_esp.1', 'moneyline'),
    ('soccer_esp.1', 'spread'),
    ('soccer_esp.1', 'total'),
    # Soccer - Serie A
    ('soccer_ita.1', 'moneyline'),
    ('soccer_ita.1', 'spread'),
    ('soccer_ita.1', 'total'),
    # Soccer - Bundesliga
    ('soccer_ger.1', 'moneyline'),
    ('soccer_ger.1', 'spread'),
    ('soccer_ger.1', 'total'),
    # Soccer - Ligue 1
    ('soccer_fra.1', 'moneyline'),
    ('soccer_fra.1', 'spread'),
    ('soccer_fra.1', 'total'),
]

def generate_synthetic_training_data(sport_key: str, market_type: str, n_samples: int = 500) -> list:
    """
    Generate synthetic training data based on sport characteristics
    This ensures we have valid training data even when ESPN API has issues
    """
    np.random.seed(42)
    
    data = []
    
    for i in range(n_samples):
        # Generate realistic team records
        home_wins = np.random.randint(10, 50)
        home_losses = np.random.randint(10, 40)
        away_wins = np.random.randint(10, 50)
        away_losses = np.random.randint(10, 40)
        
        # Calculate win percentages
        home_win_pct = home_wins / (home_wins + home_losses) if (home_wins + home_losses) > 0 else 0.5
        away_win_pct = away_wins / (away_wins + away_losses) if (away_wins + away_losses) > 0 else 0.5
        
        # Recent form (last 5 games)
        home_recent_wins = np.random.randint(0, 6)
        away_recent_wins = np.random.randint(0, 6)
        
        # Generate scores based on sport
        if 'basketball' in sport_key:
            home_score = np.random.normal(110, 12)
            away_score = np.random.normal(108, 12)
        elif 'hockey' in sport_key:
            home_score = np.random.normal(3.2, 1.2)
            away_score = np.random.normal(2.8, 1.1)
        elif 'baseball' in sport_key:
            home_score = np.random.normal(4.5, 2.5)
            away_score = np.random.normal(4.2, 2.3)
        elif 'soccer' in sport_key:
            home_score = np.random.poisson(1.4)
            away_score = np.random.poisson(1.1)
        else:  # football
            home_score = np.random.normal(24, 10)
            away_score = np.random.normal(21, 10)
        
        # Ensure non-negative scores
        home_score = max(0, home_score)
        away_score = max(0, away_score)
        
        # Create target based on market type
        if market_type == 'moneyline':
            if home_score > away_score:
                target = 1  # Home win
            elif away_score > home_score:
                target = 0  # Away win
            else:
                target = 2  # Draw (for soccer)
        elif market_type in ['spread', 'puck_line']:
            # Assume even spread for simplicity
            spread_line = 0
            home_margin = home_score - away_score + spread_line
            if home_margin > 0:
                target = 1
            elif home_margin < 0:
                target = 0
            else:
                target = 2
        elif market_type == 'total':
            # Set total line based on sport
            if 'basketball' in sport_key:
                total_line = 220
            elif 'hockey' in sport_key:
                total_line = 6
            elif 'baseball' in sport_key:
                total_line = 9
            elif 'soccer' in sport_key:
                total_line = 2.5
            else:
                total_line = 45
            
            total_score = home_score + away_score
            if total_score > total_line:
                target = 1  # Over
            elif total_score < total_line:
                target = 0  # Under
            else:
                target = 2  # Push
        else:
            target = 1 if home_score > away_score else 0
        
        # Create feature row
        row = {
            'home_wins': home_wins,
            'home_losses': home_losses,
            'away_wins': away_wins,
            'away_losses': away_losses,
            'home_recent_wins': home_recent_wins,
            'away_recent_wins': away_recent_wins,
            'home_score': int(home_score),
            'away_score': int(away_score),
            'home_points_for': home_score,
            'home_points_against': away_score,
            'away_points_for': away_score,
            'away_points_against': home_score,
            'target': target,
        }
        
        # Add soccer-specific features
        if 'soccer' in sport_key:
            row.update({
                'home_goals_for': int(home_score),
                'home_goals_against': int(away_score),
                'away_goals_for': int(away_score),
                'away_goals_against': int(home_score),
                'home_matches_played': home_wins + home_losses,
                'away_matches_played': away_wins + away_losses,
            })
        
        # Add H2H features
        row.update({
            'historical_h2h_home_wins': np.random.randint(0, 5),
            'historical_h2h_away_wins': np.random.randint(0, 5),
            'recent_h2h_wins_home': np.random.randint(0, 3),
        })
        
        # Add contextual features
        row.update({
            'home_home_wins': int(home_wins * 0.6),
            'home_home_losses': int(home_losses * 0.4),
            'home_away_wins': int(home_wins * 0.4),
            'home_away_losses': int(home_losses * 0.6),
            'away_home_wins': int(away_wins * 0.4),
            'away_home_losses': int(away_losses * 0.6),
            'away_away_wins': int(away_wins * 0.6),
            'away_away_losses': int(away_losses * 0.4),
            'home_rest_days': np.random.randint(1, 5),
            'away_rest_days': np.random.randint(1, 5),
            'home_opponent_win_pct': np.random.uniform(0.3, 0.7),
            'away_opponent_win_pct': np.random.uniform(0.3, 0.7),
            'home_injured_players': np.random.randint(0, 3),
            'away_injured_players': np.random.randint(0, 3),
            'home_injury_performance_impact': np.random.uniform(0, 0.1),
            'away_injury_performance_impact': np.random.uniform(0, 0.1),
            'temperature': np.random.randint(40, 80),
            'wind_speed': np.random.randint(0, 15),
            'precipitation': np.random.choice([0, 0, 0, 1]),  # 25% chance of precipitation
            'spread_line': 0,
            'total_line': 220 if 'basketball' in sport_key else 6 if 'hockey' in sport_key else 9 if 'baseball' in sport_key else 2.5 if 'soccer' in sport_key else 45,
        })
        
        data.append(row)
    
    return data

async def train_single_model(sport_key: str, market_type: str, ml_service: EnhancedMLService) -> dict:
    """
    Train a single model using synthetic data
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Training {sport_key} - {market_type}")
    logger.info(f"{'='*60}")
    
    try:
        # Generate synthetic training data
        logger.info(f"Generating synthetic training data for {sport_key}...")
        training_data = generate_synthetic_training_data(sport_key, market_type, n_samples=500)
        
        logger.info(f"Generated {len(training_data)} training samples")
        
        # Train models
        result = await ml_service.train_models(sport_key, market_type, training_data)
        
        if result['status'] == 'success':
            logger.info(f"✅ Successfully trained {sport_key} - {market_type}")
            logger.info(f"   Models trained: {list(result.get('model_scores', {}).keys())}")
        else:
            logger.error(f"❌ Training failed: {result.get('message', 'Unknown error')}")
        
        return {
            'sport_key': sport_key,
            'market_type': market_type,
            'status': result['status'],
            'samples': len(training_data),
            'result': result
        }
        
    except Exception as e:
        logger.error(f"❌ Error training {sport_key} - {market_type}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            'sport_key': sport_key,
            'market_type': market_type,
            'status': 'error',
            'error': str(e)
        }

async def main():
    """Main training function"""
    print("="*70)
    print("SPORTS PREDICTION MODEL TRAINING - SYNTHETIC DATA VERSION")
    print("="*70)
    
    # Initialize ML service
    ml_service = EnhancedMLService()
    
    results = []
    successful = 0
    failed = 0
    
    # Train each model
    for sport_key, market_type in TRAINING_CONFIGS:
        result = await train_single_model(sport_key, market_type, ml_service)
        results.append(result)
        
        if result['status'] == 'success':
            successful += 1
        else:
            failed += 1
        
        # Small delay between trainings
        await asyncio.sleep(0.5)
    
    # Print summary
    print("\n" + "="*70)
    print("TRAINING SUMMARY")
    print("="*70)
    print(f"Total configurations: {len(TRAINING_CONFIGS)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"Success rate: {successful/max(1, len(TRAINING_CONFIGS))*100:.1f}%")
    
    # List successful trainings
    if successful > 0:
        print("\nSuccessful trainings:")
        for r in results:
            if r['status'] == 'success':
                print(f"  ✓ {r['sport_key']} - {r['market_type']} ({r['samples']} samples)")
    
    # List failures
    if failed > 0:
        print("\nFailed trainings:")
        for r in results:
            if r['status'] == 'error':
                print(f"  ✗ {r['sport_key']} - {r['market_type']}: {r.get('error', 'Unknown error')}")
    
    print("="*70)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = Path(f"training_results_{timestamp}.json")
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': len(TRAINING_CONFIGS),
                'successful': successful,
                'failed': failed,
                'success_rate': successful/max(1, len(TRAINING_CONFIGS))
            },
            'results': results
        }, f, indent=2, default=str)
    
    print(f"\nResults saved to: {results_file}")

if __name__ == "__main__":
    asyncio.run(main())
