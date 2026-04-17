"""
Phase 5: Generate Test Predictions for Accuracy Verification
Creates sample predictions with resolved outcomes for testing accuracy metrics
"""

import sqlite3
import json
from datetime import datetime, timedelta
import random
import hashlib
from pathlib import Path
import sys

# Try PostgreSQL first, fall back to SQLite
try:
    import psycopg2
    from psycopg2.extras import execute_values
    USE_POSTGRES = True
except ImportError:
    USE_POSTGRES = False

DB_PATH = Path(__file__).parent / "backend" / "sports.db"

SPORTS = ["nba", "nfl", "mlb", "nhl", "soccer", "tennis", "mma"]
MARKET_TYPES = ["moneyline", "spread", "over_under", "player_prop"]

def generate_test_predictions(num_predictions: int = 100):
    """Generate test predictions with resolved outcomes"""
    predictions = []
    
    base_date = datetime.utcnow() - timedelta(days=60)
    
    for i in range(num_predictions):
        # Random creation date within past 60 days
        days_ago = random.randint(0, 60)
        created_at = base_date + timedelta(days=days_ago)
        resolved_at = created_at + timedelta(hours=random.randint(2, 24))
        
        sport_key = random.choice(SPORTS)
        market_type = random.choice(MARKET_TYPES)
        
        # Generate realistic confidence (varied distribution)
        confidence = random.gauss(65, 15)  # Mean 65%, std 15%
        confidence = min(95, max(50, confidence))  # Clamp to 50-95%
        
        # Outcome correlated with confidence (better high-confidence predictions)
        if random.random() < (confidence / 100):
            result = True
        else:
            result = False
        
        # Actual value (profit/loss)
        actual_value = 10 if result else -10
        
        predictions.append({
            'sport_key': sport_key,
            'market_type': market_type,
            'prediction': random.choice([0, 1]),
            'confidence': round(confidence, 2),
            'created_at': created_at.isoformat(),
            'resolved_at': resolved_at.isoformat(),
            'result': result,
            'actual_value': actual_value,
            'reasoning': f"Test prediction for {sport_key} {market_type}",
            'event_id': f"test_{i}_{hashlib.md5(str(i).encode()).hexdigest()[:8]}",
            'home_team': f"Team_{random.randint(1, 30)}",
            'away_team': f"Team_{random.randint(1, 30)}"
        })
    
    return predictions


def insert_into_sqlite(predictions: list):
    """Insert predictions into SQLite database"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # First, add missing columns if they don't exist
        print("  Checking/adding missing columns...")
        cursor.execute("PRAGMA table_info(prediction)")
        columns = {row[1] for row in cursor.fetchall()}
        
        columns_to_add = {
            'resolved_at': 'DATETIME',
            'result': 'BOOLEAN',
            'actual_value': 'FLOAT'
        }
        
        for col_name, col_type in columns_to_add.items():
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE prediction ADD COLUMN {col_name} {col_type}")
                    print(f"    ✓ Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column" not in str(e):
                        print(f"    ! Column issue: {col_name} - {e}")
        
        # Check again for required columns
        cursor.execute("PRAGMA table_info(prediction)")
        columns = {row[1] for row in cursor.fetchall()}
        
        required_columns = {'resolved_at', 'result', 'actual_value'}
        missing = required_columns - columns
        
        if missing:
            print(f"✗ Missing columns in prediction table: {missing}")
            print("  Manual fix needed for: " + ", ".join(missing))
            conn.close()
            return False
        
        # Insert predictions
        insert_count = 0
        for pred in predictions:
            try:
                cursor.execute("""
                    INSERT INTO prediction 
                    (sport_key, market_type, prediction, confidence, created_at, 
                     resolved_at, result, actual_value, reasoning, event_id, 
                     home_team, away_team)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pred['sport_key'],
                    pred['market_type'],
                    pred['prediction'],
                    pred['confidence'],
                    pred['created_at'],
                    pred['resolved_at'],
                    pred['result'],
                    pred['actual_value'],
                    pred['reasoning'],
                    pred['event_id'],
                    pred['home_team'],
                    pred['away_team']
                ))
                insert_count += 1
            except Exception as e:
                print(f"  Error inserting prediction {pred['event_id']}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"✓ Inserted {insert_count}/{len(predictions)} predictions into SQLite")
        return True
    
    except Exception as e:
        print(f"✗ Error connecting to SQLite: {e}")
        return False


def insert_into_postgres(predictions: list):
    """Insert predictions into PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            dbname="sports_predictions",
            user="postgres", 
            password="",
            host="localhost",
            port=5432
        )
        cursor = conn.cursor()
        
        # Prepare SQL
        insert_sql = """
            INSERT INTO prediction 
            (sport_key, market_type, prediction, confidence, created_at, 
             resolved_at, result, actual_value, reasoning, event_id, 
             home_team, away_team)
            VALUES %s
        """
        
        # Prepare data tuples
        values = [
            (
                p['sport_key'],
                p['market_type'],
                p['prediction'],
                p['confidence'],
                p['created_at'],
                p['resolved_at'],
                p['result'],
                p['actual_value'],
                p['reasoning'],
                p['event_id'],
                p['home_team'],
                p['away_team']
            )
            for p in predictions
        ]
        
        # Insert
        execute_values(cursor, insert_sql, values)
        conn.commit()
        
        print(f"✓ Inserted {len(predictions)} predictions into PostgreSQL")
        cursor.close()
        conn.close()
        return True
    
    except psycopg2.OperationalError:
        print("✗ Could not connect to PostgreSQL - using SQLite instead")
        return False
    except Exception as e:
        print(f"✗ Error with PostgreSQL: {e}")
        return False


def main():
    """Generate and insert test predictions"""
    print("="*60)
    print("PHASE 5: GENERATE TEST PREDICTIONS")
    print("="*60)
    
    # Parse arguments
    num_predictions = 100
    if len(sys.argv) > 1:
        try:
            num_predictions = int(sys.argv[1])
        except ValueError:
            print(f"Usage: python generate_test_predictions.py [num_predictions]")
            print(f"Using default: {num_predictions}")
    
    print(f"\n[1/2] Generating {num_predictions} test predictions...")
    predictions = generate_test_predictions(num_predictions)
    
    # Show sample
    sample = predictions[0]
    print(f"\nSample prediction:")
    print(f"  Sport: {sample['sport_key']}")
    print(f"  Market: {sample['market_type']}")
    print(f"  Confidence: {sample['confidence']}%")
    print(f"  Result: {'Win' if sample['result'] else 'Loss'}")
    print(f"  Created: {sample['created_at']}")
    print(f"  Resolved: {sample['resolved_at']}")
    
    # Calculate statistics
    win_rate = sum(1 for p in predictions if p['result']) / len(predictions) * 100
    avg_confidence = sum(p['confidence'] for p in predictions) / len(predictions)
    roi = sum(p['actual_value'] for p in predictions) / len(predictions)
    
    print(f"\nPredictions Statistics:")
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Avg Confidence: {avg_confidence:.1f}%")
    print(f"  Avg ROI: {roi:+.1f}%")
    
    # Insert into database
    print(f"\n[2/2] Inserting into database...")
    
    success = False
    if USE_POSTGRES:
        success = insert_into_postgres(predictions)
    
    if not success:
        success = insert_into_sqlite(predictions)
    
    if success:
        print(f"\n✓ Test data generation complete!")
        print(f"  Now run: python phase5_verification_suite.py")
        return 0
    else:
        print(f"\n✗ Failed to insert predictions")
        return 1


if __name__ == "__main__":
    sys.exit(main())
