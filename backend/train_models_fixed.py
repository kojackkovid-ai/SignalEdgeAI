#!/usr/bin/env python3
"""
Fixed Model Training Script
Properly processes ESPN data and creates training targets
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.enhanced_ml_service import EnhancedMLService
from app.services.data_preprocessing import AdvancedFeatureEngineer
from app.services.espn_prediction_service import ESPNPredictionService

# Configure logging
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

def create_target_variable(df: pd.DataFrame, market_type: str) -> pd.Series:
    """
    Create target variable from game scores based on market type
    """
    try:
        if market_type == 'moneyline':
            # 1 = home win, 0 = away win, 2 = draw
            conditions = [
                df['home_score'] > df['away_score'],
                df['home_score'] < df['away_score'],
                df['home_score'] == df['away_score']
            ]
            choices = [1, 0, 2]
            return np.select(conditions, choices, default=1)
        
        elif market_type == 'spread' or market_type == 'puck_line':
            # For spread, we need the spread line
            # If no spread_line column, assume even spread (0)
            spread_line = df.get('spread_line', 0)
            home_margin = df['home_score'] - df['away_score'] + spread_line
            # 1 = home covers, 0 = away covers, 2 = push
            conditions = [
                home_margin > 0,
                home_margin < 0,
                home_margin == 0
            ]
            choices = [1, 0, 2]
            return np.select(conditions, choices, default=1)
        
        elif market_type == 'total':
            # For totals, we need the total line
            # If no total_line column, estimate from average
            total_line = df.get('total_line', 200)
            total_score = df['home_score'] + df['away_score']
            # 1 = over, 0 = under, 2 = push
            conditions = [
                total_score > total_line,
                total_score < total_line,
                total_score == total_line
            ]
            choices = [1, 0, 2]
            return np.select(conditions, choices, default=1)
        
        else:
            # Default to moneyline
            return (df['home_score'] > df['away_score']).astype(int)
    
    except Exception as e:
        logger.error(f"Error creating target variable: {e}")
        # Fallback: assume home win
        return pd.Series([1] * len(df), index=df.index)

def prepare_training_features(df: pd.DataFrame, sport_key: str) -> pd.DataFrame:
    """
    Prepare training features from raw ESPN game data
    """
    features = pd.DataFrame(index=df.index)
    
    # Parse records (e.g., "45-20" -> wins=45, losses=20)
    def parse_record(record_str):
        try:
            if pd.isna(record_str) or record_str == '0-0':
                return 0, 0
            parts = str(record_str).split('-')
            if len(parts) == 2:
                return int(parts[0]), int(parts[1])
        except:
            pass
        return 0, 0
    
    # Home team records
    home_wins, home_losses = zip(*df['home_record'].apply(parse_record))
    features['home_wins'] = home_wins
    features['home_losses'] = home_losses
    
    # Away team records
    away_wins, away_losses = zip(*df['away_record'].apply(parse_record))
    features['away_wins'] = away_wins
    features['away_losses'] = away_losses
    
    # Recent form (convert 0-1 scale to approximate wins in last 5)
    features['home_recent_wins'] = (df.get('home_form', 0.5) * 5).round().astype(int)
    features['away_recent_wins'] = (df.get('away_form', 0.5) * 5).round().astype(int)
    
    # Scores
    features['home_score'] = df['home_score'].astype(int)
    features['away_score'] = df['away_score'].astype(int)
    
    # Add placeholder features for model compatibility
    # These will be filled with defaults or computed from available data
    features['home_points_for'] = features['home_score']
    features['home_points_against'] = features['away_score']
    features['away_points_for'] = features['away_score']
    features['away_points_against'] = features['home_score']
    
    # Soccer-specific features
    if 'soccer' in sport_key:
        features['home_goals_for'] = features['home_score']
        features['home_goals_against'] = features['away_score']
        features['away_goals_for'] = features['away_score']
        features['away_goals_against'] = features['home_score']
        features['home_matches_played'] = features['home_wins'] + features['home_losses']
        features['away_matches_played'] = features['away_wins'] + features['away_losses']
    
    # Historical H2H features (placeholders)
    features['historical_h2h_home_wins'] = 0
    features['historical_h2h_away_wins'] = 0
    features['recent_h2h_wins_home'] = 0
    
    # Contextual features
    features['home_home_wins'] = (features['home_wins'] * 0.6).round().astype(int)  # Assume 60% home wins
    features['home_home_losses'] = (features['home_wins'] * 0.4).round().astype(int)
    features['home_away_wins'] = (features['home_wins'] * 0.4).round().astype(int)
    features['home_away_losses'] = (features['home_wins'] * 0.6).round().astype(int)
    
    features['away_home_wins'] = (features['away_wins'] * 0.4).round().astype(int)
    features['away_home_losses'] = (features['away_wins'] * 0.6).round().astype(int)
    features['away_away_wins'] = (features['away_wins'] * 0.6).round().astype(int)
    features['away_away_losses'] = (features['away_wins'] * 0.4).round().astype(int)
    
    # Rest days (default to 2)
    features['home_rest_days'] = 2
    features['away_rest_days'] = 2
    
    # Strength of schedule (default to 0.5)
    features['home_opponent_win_pct'] = 0.5
    features['away_opponent_win_pct'] = 0.5
    
    # Injury placeholders
    features['home_injured_players'] = 0
    features['away_injured_players'] = 0
    features['home_injury_performance_impact'] = 0.0
    features['away_injury_performance_impact'] = 0.0
    
    # Weather placeholders
    features['temperature'] = 70
    features['wind_speed'] = 5
    features['precipitation'] = 0
    
    # Market lines (placeholders, will be updated if available in odds)
    features['spread_line'] = 0
    features['total_line'] = 200
    
    return features

async def train_single_model(sport_key: str, market_type: str, ml_service: EnhancedMLService, espn_service: ESPNPredictionService) -> dict:
    """
    Train a single model for a sport/market combination
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Training {sport_key} - {market_type}")
    logger.info(f"{'='*60}")
    
    try:
        # Fetch historical data
        logger.info(f"Fetching historical data for {sport_key}...")
        historical_games = await espn_service.get_historical_data(
            sport_key=sport_key,
            days_back=90  # Get 90 days of data
        )
        
        if not historical_games or len(historical_games) < 50:
            logger.warning(f"Insufficient data: {len(historical_games) if historical_games else 0} games")
            return {
                'sport_key': sport_key,
                'market_type': market_type,
                'status': 'skipped',
                'reason': 'insufficient_data'
            }
        
        logger.info(f"Retrieved {len(historical_games)} games")
        
        # Convert to DataFrame
        df = pd.DataFrame(historical_games)
        
        # Filter completed games with valid scores
        df = df[df['status'].isin(['STATUS_FINAL', 'STATUS_COMPLETED'])]
        df = df.dropna(subset=['home_score', 'away_score'])
        
        if len(df) < 50:
            logger.warning(f"After filtering, only {len(df)} valid games remain")
            return {
                'sport_key': sport_key,
                'market_type': market_type,
                'status': 'skipped',
                'reason': 'insufficient_valid_games'
            }
        
        logger.info(f"Processing {len(df)} valid completed games")
        
        # Prepare features
        features_df = prepare_training_features(df, sport_key)
        
        # Create target variable
        target = create_target_variable(df, market_type)
        features_df['target'] = target
        
        # Convert to list of dicts for the ML service
        training_data = features_df.to_dict('records')
        
        logger.info(f"Prepared {len(training_data)} training samples with {len(features_df.columns)} features")
        
        # Train models
        result = await ml_service.train_models(sport_key, market_type, training_data)
        
        if result['status'] == 'success':
            logger.info(f"✅ Successfully trained {sport_key} - {market_type}")
            logger.info(f"   Models trained: {result.get('model_scores', {}).keys()}")
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
    print("SPORTS PREDICTION MODEL TRAINING - FIXED VERSION")
    print("="*70)
    
    # Initialize services
    ml_service = EnhancedMLService()
    espn_service = ESPNPredictionService()
    
    results = []
    successful = 0
    failed = 0
    skipped = 0
    
    # Train each model
    for sport_key, market_type in TRAINING_CONFIGS:
        result = await train_single_model(sport_key, market_type, ml_service, espn_service)
        results.append(result)
        
        if result['status'] == 'success':
            successful += 1
        elif result['status'] == 'error':
            failed += 1
        else:
            skipped += 1
        
        # Small delay between trainings
        await asyncio.sleep(1)
    
    # Close ESPN service
    await espn_service.close()
    
    # Print summary
    print("\n" + "="*70)
    print("TRAINING SUMMARY")
    print("="*70)
    print(f"Total configurations: {len(TRAINING_CONFIGS)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Skipped: {skipped}")
    
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
    
    # List skipped
    if skipped > 0:
        print("\nSkipped trainings:")
        for r in results:
            if r['status'] == 'skipped':
                print(f"  ⚠ {r['sport_key']} - {r['market_type']}: {r.get('reason', 'Unknown reason')}")
    
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
                'skipped': skipped
            },
            'results': results
        }, f, indent=2, default=str)
    
    print(f"\nResults saved to: {results_file}")

if __name__ == "__main__":
    asyncio.run(main())
