#!/usr/bin/env python3
"""
Check database structure and add test data if needed
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

db_path = Path("sports_predictions.db")

print("=" * 80)
print("DATABASE STRUCTURE CHECK")
print("=" * 80)

if db_path.exists():
    print(f"\n✅ Database exists at: {db_path}")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"\n📊 Tables in database:")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  ✓ {table_name} ({count} rows)")
    
    # Check predictions table structure
    print(f"\n📋 Predictions table columns:")
    cursor.execute("PRAGMA table_info(predictions);")
    columns = cursor.fetchall()
    for col in columns:
        name, dtype = col[1], col[2]
        print(f"  - {name} ({dtype})")
    
    # Check resolved predictions
    cursor.execute("SELECT COUNT(*) FROM predictions WHERE resolved_at IS NOT NULL")
    resolved = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM predictions")
    total = cursor.fetchone()[0]
    print(f"\n📈 Predictions status:")
    print(f"  Total: {total}")
    print(f"  Resolved: {resolved}")
    print(f"  Unresolved: {total - resolved}")
    
    conn.close()
else:
    print(f"\n❌ Database not found at: {db_path}")

print("\n" + "=" * 80)
print("Would you like to add test data? (y/n)")
print("=" * 80)

response = input().strip().lower()

if response == 'y':
    print("\nAdding test predictions...")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Insert 20 test predictions
    count = 0
    for i in range(20):
        try:
            cursor.execute("""
            INSERT INTO predictions 
            (id, sport, matchup, prediction, confidence, odds, prediction_type, 
             created_at, resolved_at, result, actual_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"test_{datetime.now().timestamp()}_{i}",
                ["basketball_nba", "americanfootball_nfl", "icehockey_nhl"][i % 3],
                f"Team A vs Team B (Test {i})",
                "Team A",
                55 + (i % 30),
                "+110",
                "moneyline",
                (datetime.now() - timedelta(days=int(i/5))).isoformat(),
                (datetime.now() - timedelta(days=int(i/5))).isoformat(),
                "win" if i % 2 == 0 else "loss",
                105 if i % 2 == 0 else 98
            ))
            count += 1
        except Exception as e:
            print(f"Error inserting prediction {i}: {e}")
    
    conn.commit()
    print(f"✅ Added {count} test predictions\n")
    
    # Show new counts
    cursor.execute("SELECT COUNT(*) FROM predictions")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM predictions WHERE resolved_at IS NOT NULL")
    resolved = cursor.fetchone()[0]
    print(f"📈 Updated counts:")
    print(f"  Total: {total}")
    print(f"  Resolved: {resolved}")
    
    conn.close()
    
    print("\n✅ Now run the audit:")
    print("  python audit_accuracy_simple.py --days 30")
else:
    print("\nSkipped adding test data.")
