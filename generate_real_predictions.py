#!/usr/bin/env python3
"""
Generate real predictions from the backend API and store in database.
Uses live ESPN data to create actual predictions.
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys

# Configuration
API_URL = "http://127.0.0.1:8000"
SPORTS_MARKETS = {
    'basketball_nba': ['moneyline', 'spread', 'total'],
    'americanfootball_nfl': ['moneyline', 'spread', 'total'],
    'icehockey_nhl': ['moneyline', 'puck_line', 'total'],
    'baseball_mlb': ['moneyline', 'total'],
}

def get_upcoming_games(days_ahead: int = 7) -> list:
    """Fetch upcoming games from ESPN data."""
    try:
        response = requests.get(f"{API_URL}/api/games", params={
            "days_ahead": days_ahead
        }, timeout=30)
        
        if response.status_code == 200:
            games = response.json()
            print(f"✓ Found {len(games)} upcoming games")
            return games
        else:
            print(f"✗ Error fetching games: {response.status_code}")
            return []
    except Exception as e:
        print(f"✗ Error fetching games: {e}")
        return []

def create_prediction(sport_key: str, market_type: str, game_data: dict) -> dict:
    """Create a prediction for a specific game."""
    try:
        payload = {
            "sport_key": sport_key,
            "market_type": market_type,
            "game_data": game_data
        }
        
        response = requests.post(
            f"{API_URL}/api/predictions/create",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                'status': 'success',
                'prediction': result.get('prediction'),
                'confidence': result.get('confidence'),
                'sport_key': sport_key,
                'market_type': market_type
            }
        else:
            return {
                'status': 'error',
                'message': f'Status {response.status_code}',
                'sport_key': sport_key,
                'market_type': market_type
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'sport_key': sport_key,
            'market_type': market_type
        }

def generate_predictions_batch(games: list, batch_size: int = 50) -> int:
    """Generate predictions for all games and markets."""
    total_predictions = 0
    batch_count = 0
    
    print(f"\n{'='*70}")
    print("GENERATING REAL PREDICTIONS")
    print(f"{'='*70}\n")
    
    for game_index, game in enumerate(games[:batch_size], 1):
        game_id = game.get('id', f"game_{game_index}")
        home_team = game.get('home_team', 'Home')
        away_team = game.get('away_team', 'Away')
        sport_key = game.get('sport_key', 'unknown')
        
        print(f"\nGame {game_index}: {away_team} @ {home_team} ({sport_key})")
        
        # Get market types for this sport
        market_types = SPORTS_MARKETS.get(sport_key, ['moneyline'])
        
        for market_type in market_types:
            try:
                print(f"  • Predicting {market_type}...", end=" ", flush=True)
                
                result = create_prediction(sport_key, market_type, game)
                
                if result['status'] == 'success':
                    confidence = result.get('confidence', 0)
                    prediction = result.get('prediction', 'unknown')
                    print(f"✓ {prediction} ({confidence:.1f}%)")
                    total_predictions += 1
                else:
                    print(f"✗ {result.get('message', 'Unknown error')}")
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"✗ Exception: {e}")
        
        batch_count += 1
    
    return total_predictions

def main():
    print("\n" + "="*70)
    print("REAL PREDICTION GENERATION TOOL")
    print("="*70)
    
    # Check if API is running
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        print(f"\n✓ Backend API is running: {API_URL}")
    except:
        print(f"\n✗ Backend API not running at {API_URL}")
        print("  Start the backend with: python start_backend.py")
        return 1
    
    # Get upcoming games
    print("\nFetching upcoming games...")
    games = get_upcoming_games(days_ahead=7)
    
    if not games:
        print("✗ No games found. Try again later.")
        return 1
    
    # Generate predictions
    total = generate_predictions_batch(games, batch_size=50)
    
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"✓ Generated {total} real predictions")
    print(f"✓ Predictions stored in database")
    print(f"\nNext step: Run audit to see accuracy")
    print(f"  python audit_accuracy_simple.py --days 30")
    print(f"{'='*70}\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
