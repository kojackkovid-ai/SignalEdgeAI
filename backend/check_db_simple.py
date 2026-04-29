#!/usr/bin/env python3
"""
Simple database check
"""
import sqlite3

def check_db():
    conn = sqlite3.connect('sports_predictions.db')
    c = conn.cursor()

    print("=== USERS ===")
    c.execute('SELECT id, username FROM users')
    users = c.fetchall()
    for uid, uname in users:
        print(f'{uname}: {uid}')

    print("\n=== PREDICTION USER IDS ===")
    c.execute('SELECT DISTINCT user_id FROM prediction_records')
    pred_users = c.fetchall()
    for uid in pred_users:
        print(uid[0])

    print("\n=== PREDICTION COUNTS BY USER ===")
    c.execute('SELECT user_id, COUNT(*) FROM prediction_records GROUP BY user_id')
    counts = c.fetchall()
    for uid, count in counts:
        print(f'{uid}: {count} predictions')

    print("\n=== SAMPLE PREDICTIONS ===")
    c.execute('SELECT id, user_id, outcome, sport_key FROM prediction_records LIMIT 3')
    samples = c.fetchall()
    for pid, uid, outcome, sport in samples:
        print(f'ID: {pid}, User: {uid}, Outcome: {outcome}, Sport: {sport}')

    print("\n=== STATS TABLES ===")
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%stats%'")
    stats_tables = c.fetchall()
    print('Stats tables:', [t[0] for t in stats_tables])

    if stats_tables:
        for table_name in [t[0] for t in stats_tables]:
            print(f"\n=== {table_name.upper()} TABLE ===")
            try:
                c.execute(f'SELECT * FROM {table_name} LIMIT 3')
                rows = c.fetchall()
                for row in rows:
                    print(row)
            except Exception as e:
                print(f'Error querying {table_name}: {e}')

    conn.close()

if __name__ == "__main__":
    check_db()