#!/usr/bin/env python3
"""
Train ALL ML models using ONLY real ESPN data
- NO synthetic data fallback
- Real historical data from ESPN API
- All sports: NBA, NFL, MLB, NHL, 6 Soccer leagues
- 3 markets per sport where applicable
- 3 algorithms per market: xgboost, random_forest, gradient_boosting
"""

import asyncio
import logging
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# Add backend to path
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
        logging.FileHandler('training_final.log')
    ]
)
logger = logging.getLogger(__name__)

# Training configurations - ALL sports and markets
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
    # Soccer - 6 leagues
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

# ESPN sport mappings
ESPN_SPORT_MAP = {
    'basketball_nba': 'basketball/nba',
    'americanfootball_nfl': 'football/nfl',
    'baseball_mlb': 'baseball/mlb',
    'icehockey_nhl': 'hockey/nhl',
    'soccer_epl': 'soccer/eng.1',
    'soccer_usa_mls': 'soccer/usa.1',
    'soccer_esp.1': 'soccer/esp.1',
    'soccer_ita.1': 'soccer/ita.1',
    'soccer_ger.1': 'soccer/ger.1',
    'soccer_fra.1': 'soccer/fra.1',
}


async def fetch_espn_historical_games(espn_service: ESPNPredictionService, sport_key: str, days_back: int = 90) -> List[Dict]:
    """
    Fetch real historical games from ESPN API
    NO synthetic fallback - returns empty list if ESPN fails
    """
    espn_path = ESPN_SPORT_MAP.get(sport_key)
    if not espn_path:
        logger.error(f"No ESPN mapping for {sport_key}")
        return []
    
    logger.info(f"Fetching ESPN data for {sport_key} ({espn_path}) - last {days_back} days")
    
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Fetch games from ESPN
        games = await espn_service.get_historical_data(
            sport_key=sport_key,
            days_back=days_back
        )

        
        if not games:
            logger.warning(f"No games returned from ESPN for {sport_key}")
            return []
        
        logger.info(f"Fetched {len(games)} games from ESPN for {sport_key}")
        
        # Transform to training format
        training_games = []
        for game in games:
            try:
                # Extract scores
                home_score = game.get('home_score', 0)
                away_score = game.get('away_score', 0)
                
                if home_score is None or away_score is None:
                    continue
                
                # Build training record
                training_game = {
                    'home_team': game.get('home_team', ''),
                    'away_team': game.get('away_team', ''),
                    'home_score': float(home_score),
                    'away_score': float(away_score),
                    'game_date': game.get('date', ''),
                    # Record features
                    'home_wins': game.get('home_record', {}).get('wins', 0),
                    'home_losses': game.get('home_record', {}).get('losses', 0),
                    'away_wins': game.get('away_record', {}).get('wins', 0),
                    'away_losses': game.get('away_record', {}).get('losses', 0),
                    # Recent form
                    'home_recent_wins': game.get('home_recent_form', 2),
                    'away_recent_wins': game.get('away_recent_form', 2),
                    # Stats
                    'home_points_for': game.get('home_stats', {}).get('points_for', 0),
                    'home_points_against': game.get('home_stats', {}).get('points_against', 0),
                    'away_points_for': game.get('away_stats', {}).get('points_for', 0),
                    'away_points_against': game.get('away_stats', {}).get('points_against', 0),
                    # Rest days
                    'home_rest_days': game.get('home_rest_days', 2),
                    'away_rest_days': game.get('away_rest_days', 2),
                    # Opponent strength
                    'home_opponent_win_pct': game.get('home_opponent_win_pct', 0.5),
                    'away_opponent_win_pct': game.get('away_opponent_win_pct', 0.5),
                }
                
                # Add sport-specific fields
                if sport_key.startswith('soccer_'):
                    training_game['home_goals_for'] = game.get('home_stats', {}).get('goals_for', 0)
                    training_game['home_goals_against'] = game.get('home_stats', {}).get('goals_against', 0)
                    training_game['away_goals_for'] = game.get('away_stats', {}).get('goals_for', 0)
                    training_game['away_goals_against'] = game.get('away_stats', {}).get('goals_against', 0)
                
                training_games.append(training_game)
                
            except Exception as e:
                logger.warning(f"Error processing game: {e}")
                continue
        
        logger.info(f"Processed {len(training_games)} valid training games for {sport_key}")
        return training_games
        
    except Exception as e:
        logger.error(f"Error fetching ESPN data for {sport_key}: {e}")
        return []


async def train_models_for_config(ml_service: EnhancedMLService, sport_key: str, market_type: str, 
                                  games_data: List[Dict]) -> Dict[str, Any]:
    """
    Train models for a specific sport/market configuration
    """
    logger.info(f"Training {sport_key} - {market_type} with {len(games_data)} games")
    
    try:
        if len(games_data) < 50:
            logger.error(f"Insufficient data for {sport_key} - {market_type}: {len(games_data)} games (need 50+)")
            return {
                'sport_key': sport_key,
                'market_type': market_type,
                'status': 'error',
                'error': f'Insufficient data: {len(games_data)} games'
            }
        
        # Train models using EnhancedMLService
        result = await ml_service.train_models(
            sport_key=sport_key,
            market_type=market_type,
            training_data=games_data
        )
        
        if result.get('status') == 'success':
            logger.info(f"[OK] Successfully trained {sport_key} - {market_type}")
            return {
                'sport_key': sport_key,
                'market_type': market_type,
                'status': 'success',
                'model_scores': result.get('model_scores', {}),
                'games_used': len(games_data)
            }
        else:
            logger.error(f"Training failed for {sport_key} - {market_type}: {result.get('message')}")
            return {
                'sport_key': sport_key,
                'market_type': market_type,
                'status': 'error',
                'error': result.get('message', 'Unknown error')
            }
            
    except Exception as e:
        logger.error(f"Exception training {sport_key} - {market_type}: {e}")
        return {
            'sport_key': sport_key,
            'market_type': market_type,
            'status': 'error',
            'error': str(e)
        }


async def train_all_models():
    """
    Main training loop - trains all configurations with real ESPN data only
    """
    logger.info("=" * 70)
    logger.info("STARTING COMPLETE MODEL TRAINING - REAL ESPN DATA ONLY")
    logger.info("=" * 70)
    
    # Initialize services
    ml_service = EnhancedMLService()
    espn_service = ESPNPredictionService()
    
    results = []
    successful = 0
    failed = 0
    
    # Track ESPN data availability
    espn_data_stats = {}
    
    for sport_key, market_type in TRAINING_CONFIGS:
        logger.info(f"\n{'='*70}")
        logger.info(f"Processing: {sport_key} - {market_type}")
        logger.info(f"{'='*70}")
        
        # Fetch real ESPN data
        games_data = await fetch_espn_historical_games(espn_service, sport_key, days_back=90)
        
        # Track data availability
        if sport_key not in espn_data_stats:
            espn_data_stats[sport_key] = {'games': len(games_data), 'markets': []}
        espn_data_stats[sport_key]['markets'].append(market_type)
        
        if not games_data:
            logger.error(f"NO ESPN DATA for {sport_key} - cannot train {market_type}")
            results.append({
                'sport_key': sport_key,
                'market_type': market_type,
                'status': 'error',
                'error': 'No ESPN data available'
            })
            failed += 1
            continue
        
        # Train models
        result = await train_models_for_config(ml_service, sport_key, market_type, games_data)
        results.append(result)
        
        if result['status'] == 'success':
            successful += 1
        else:
            failed += 1
    
    # Close ESPN service
    await espn_service.close()
    
    # Generate report
    logger.info(f"\n{'='*70}")
    logger.info("TRAINING COMPLETE - FINAL REPORT")
    logger.info(f"{'='*70}")
    logger.info(f"Total configurations: {len(TRAINING_CONFIGS)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success rate: {successful/len(TRAINING_CONFIGS)*100:.1f}%")
    
    logger.info(f"\nESPN Data Availability:")
    for sport, stats in espn_data_stats.items():
        logger.info(f"  {sport}: {stats['games']} games for markets: {stats['markets']}")
    
    # Save detailed report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_configs': len(TRAINING_CONFIGS),
        'successful': successful,
        'failed': failed,
        'success_rate': successful / len(TRAINING_CONFIGS) if TRAINING_CONFIGS else 0,
        'espn_data_stats': espn_data_stats,
        'results': results
    }
    
    report_path = Path('training_report_final.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"\nReport saved to: {report_path}")
    logger.info(f"{'='*70}")
    
    return successful, failed


if __name__ == "__main__":
    try:
        successful, failed = asyncio.run(train_all_models())
        
        if successful > 0:
            print(f"\n[OK] Training complete! {successful} models trained successfully.")
            sys.exit(0)
        else:
            print(f"\n[ERROR] All trainings failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n[ERROR] Training failed: {e}")
        sys.exit(1)
