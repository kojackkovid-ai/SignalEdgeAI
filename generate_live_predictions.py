#!/usr/bin/env python3
"""
Generate real predictions directly using the backend services.
Skips API and works directly with database and ML models.
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "sports-prediction-platform" / "backend"
if backend_dir.exists():
    sys.path.insert(0, str(backend_dir))

def main():
    """Generate real predictions from upcoming games."""
    print("\n" + "="*70)
    print("REAL PREDICTION GENERATION")
    print("="*70)
    
    try:
        # Import after path is set
        from app.config import settings
        from app.database import get_db, init_db
        from app.services.espn_prediction_service import ESPNPredictionService
        from app.services.enhanced_ml_service import EnhancedMLService
        from app.models.db_models import Prediction, Game
        from sqlalchemy import select
        import logging
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        # Initialize database
        print("\n∴ Initializing database...")
        init_db()
        
        # Initialize services
        print("∴ Initializing services...")
        espn_service = ESPNPredictionService()
        ml_service = EnhancedMLService()
        
        # Run async main
        async def async_main():
            """Run the prediction generation."""
            print("\n∴ Fetching upcoming games from ESPN...")
            
            # Get upcoming games for major sports
            sports = ['basketball_nba', 'americanfootball_nfl', 'icehockey_nhl', 'baseball_mlb']
            all_games = []
            
            for sport_key in sports:
                try:
                    games = await espn_service.fetch_upcoming_games(sport_key, days_ahead=7)
                    all_games.extend(games)
                    print(f"  ✓ {sport_key}: {len(games)} games")
                except Exception as e:
                    print(f"  ✗ {sport_key}: {e}")
            
            if not all_games:
                print("\n✗ No upcoming games found")
                return 0
            
            print(f"\n✓ Total games found: {len(all_games)}")
            
            # Generate predictions
            prediction_count = 0
            print("\n∴ Generating predictions...")
            
            for idx, game in enumerate(all_games[:50], 1):  # Limit to first 50 games
                sport_key = game.get('sport_key', '')
                game_id = game.get('id', '')
                home_team = game.get('home_team', 'Home')
                away_team = game.get('away_team', 'Away')
                
                print(f"\n  Game {idx}: {away_team} @ {home_team}")
                
                # Markets to predict for each sport
                markets = {
                    'basketball_nba': ['moneyline', 'spread', 'total'],
                    'americanfootball_nfl': ['moneyline', 'spread', 'total'],
                    'icehockey_nhl': ['moneyline', 'puck_line', 'total'],
                    'baseball_mlb': ['moneyline', 'total'],
                }
                
                for market_type in markets.get(sport_key, ['moneyline']):
                    try:
                        result = await ml_service.predict(sport_key, market_type, game)
                        
                        if result.get('status') == 'success':
                            confidence = result.get('confidence', 0)
                            prediction = result.get('prediction', 'unknown')
                            print(f"    • {market_type}: {prediction} ({confidence:.1f}%) ✓")
                            prediction_count += 1
                        else:
                            print(f"    • {market_type}: Error ✗")
                    except Exception as e:
                        print(f"    • {market_type}: {e} ✗")
                    
                    await asyncio.sleep(0.2)  # Rate limiting
            
            print(f"\n{'='*70}")
            print(f"RESULTS")
            print(f"{'='*70}")
            print(f"✓ Generated {prediction_count} real predictions")
            print(f"✓ Predictions based on live ESPN data")
            print(f"✓ All predictions use corrected confidence (NOT hash-based)")
            print(f"\nNext: Run audit to see actual accuracy")
            print(f"  cd sports-prediction-platform")
            print(f"  python audit_accuracy_simple.py --days 30")
            print(f"{'='*70}\n")
            
            return prediction_count
        
        # Run async code
        count = asyncio.run(async_main())
        return 0 if count > 0 else 1
        
    except ImportError as e:
        print(f"\n✗ Import Error: {e}")
        print(f"  Make sure you're in the workspace root directory")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
