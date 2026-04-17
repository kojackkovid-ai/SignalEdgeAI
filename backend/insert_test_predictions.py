"""
Direct database insertion of test predictions for analytics
"""
import sqlite3
import uuid
from datetime import datetime, timedelta
import json

db_path = "sports_predictions.db"
now = datetime.utcnow()

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create test predictions table if needed
    test_predictions = []
    
    # NBA predictions (10)
    for i in range(10):
        pred_id = str(uuid.uuid4())
        result = 'win' if i % 2 == 0 else 'loss'
        test_predictions.append((
            pred_id,  # id
            'NBA',  # sport
            'NBA',  # league
            f'test-match-{i}',  # matchup
            'Test Prediction',  # prediction
            70 + i,  # confidence
            'moneyline',  # prediction_type
            'basketball_nba',  # sport_key
            (now - timedelta(days=7-i)).isoformat(),  # created_at
            (now - timedelta(days=6-i)).isoformat(),  # resolved_at
            result,  # result
            105.0 + i,  # actual_value
            json.dumps([]),  # reasoning
            json.dumps({}),  # model_weights
            (now - timedelta(days=7-i)).isoformat(),  # updated_at
        ))
    
    # NFL predictions (5)
    for i in range(5):
        pred_id = str(uuid.uuid4())
        result = 'win' if i % 2 == 0 else 'loss'
        test_predictions.append((
            pred_id,
            'NFL',
            'NFL',
            f'test-nfl-{i}',
            'NFL Test',
            65 + i,
            'moneyline',
            'americanfootball_nfl',
            (now - timedelta(days=5-i)).isoformat(),
            (now - timedelta(days=4-i)).isoformat(),
            result,
            25.0 + i,
            json.dumps([]),
            json.dumps({}),
            (now - timedelta(days=5-i)).isoformat(),
        ))
    
    # Insert into database
    insert_sql = """
    INSERT INTO predictions (
        id, sport, league, matchup, prediction, confidence, prediction_type,
        sport_key, created_at, resolved_at, result, actual_value,
        reasoning, model_weights, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    cursor.executemany(insert_sql, test_predictions)
    conn.commit()
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM predictions WHERE resolved_at IS NOT NULL")
    resolved_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM predictions")
    total_count = cursor.fetchone()[0]
    
    print(f"✓ Inserted {len(test_predictions)} test predictions")
    print(f"✓ Total predictions in DB: {total_count}")
    print(f"✓ Resolved predictions: {resolved_count}")
    
    # Show breakdown
    cursor.execute("""
    SELECT sport, COUNT(*) as total, 
           SUM(CASE WHEN result='win' THEN 1 ELSE 0 END) as wins
    FROM predictions
    WHERE resolved_at IS NOT NULL
    GROUP BY sport
    """)
    
    print("\n✓ Breakdown by sport:")
    for row in cursor.fetchall():
        sport, total, wins = row
        wr = (wins / total * 100) if total > 0 else 0
        print(f"  - {sport}: {wins}/{total} wins ({wr:.1f}% win rate)")
    
    conn.close()
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
