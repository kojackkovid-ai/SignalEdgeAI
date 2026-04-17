"""
Phase 5: Initialize Prediction Table Schema
Creates prediction table with all required columns
"""

import sqlite3
from pathlib import Path
import sys

DB_PATH = Path(__file__).parent / "backend" / "sports.db"

def create_prediction_table():
    """Create prediction table with outcome tracking columns"""
    try:
        # Ensure directory exists
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='prediction'
        """)
        
        if cursor.fetchone():
            print(f"✓ Prediction table already exists")
            conn.close()
            return True
        
        # Create prediction table with all required columns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prediction (
                id TEXT PRIMARY KEY,
                sport_key TEXT,
                market_type TEXT,
                prediction INTEGER,
                confidence FLOAT,
                created_at DATETIME,
                resolved_at DATETIME,
                result BOOLEAN,
                actual_value FLOAT,
                reasoning TEXT,
                event_id TEXT,
                home_team TEXT,
                away_team TEXT,
                sport TEXT,
                league TEXT,
                matchup TEXT,
                prediction_type TEXT,
                player TEXT,
                market_key TEXT,
                point FLOAT,
                game_time TEXT,
                model_weights TEXT,
                odds TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        
        print(f"✓ Created prediction table with all columns")
        return True
    
    except Exception as e:
        print(f"✗ Error creating table: {e}")
        return False


def main():
    """Initialize database schema"""
    print("="*60)
    print("PHASE 5: INITIALIZE DATABASE SCHEMA")
    print("="*60)
    
    print(f"\nTarget database: {DB_PATH}")
    print("\n[1/1] Creating prediction table...")
    
    if create_prediction_table():
        print(f"\n✓ Schema initialization complete!")
        return 0
    else:
        print(f"\n✗ Schema initialization failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
