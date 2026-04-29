#!/usr/bin/env python3
"""
Comprehensive accuracy dashboard verification script
Checks database, predictions, users, and calculates metrics
"""
import sqlite3
import json
from datetime import datetime, timedelta

def verify_database():
    """Verify database integrity and user-prediction associations"""
    conn = sqlite3.connect('sports_predictions.db')
    c = conn.cursor()
    
    print("\n" + "="*70)
    print("ACCURACY DASHBOARD VERIFICATION REPORT")
    print("="*70)
    
    # Check tables exist
    print("\n📋 TABLE VERIFICATION")
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in c.fetchall()]
    print(f"✓ Tables found: {', '.join(tables)}")
    
    # Check prediction records
    print("\n📊 PREDICTION RECORDS")
    c.execute('SELECT COUNT(*) FROM prediction_records')
    total_preds = c.fetchone()[0]
    print(f"  Total records: {total_preds}")
    
    c.execute('SELECT outcome, COUNT(*) FROM prediction_records GROUP BY outcome')
    for outcome, count in c.fetchall():
        print(f"    {outcome}: {count}")
    
    # Check users
    print("\n👥 USER DATA")
    c.execute('SELECT COUNT(*) FROM users')
    user_count = c.fetchone()[0]
    print(f"  Total users: {user_count}")
    
    if user_count > 0:
        c.execute('SELECT id, username, total_predictions, win_rate, roi FROM users LIMIT 10')
        for user_id, username, total, win_rate, roi in c.fetchall():
            print(f"  - {username}: {total} predictions, {win_rate:.1%} win rate, {roi:.1f}% ROI")
    
    # Check user-prediction associations
    print("\n🔗 USER-PREDICTION ASSOCIATIONS")
    c.execute('SELECT user_id, COUNT(*) FROM prediction_records WHERE user_id IS NOT NULL GROUP BY user_id')
    user_pred_counts = c.fetchall()
    if user_pred_counts:
        for user_id, count in user_pred_counts:
            c.execute('SELECT username FROM users WHERE id = ?', (user_id,))
            user_info = c.fetchone()
            username = user_info[0] if user_info else "Unknown"
            print(f"  - User {username} ({user_id}): {count} predictions")
    else:
        print("  ⚠️ No user-prediction associations found!")
    
    # Calculate overall metrics
    print("\n📈 OVERALL METRICS")
    c.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN outcome='hit' THEN 1 ELSE 0 END) as hits,
            SUM(CASE WHEN outcome='miss' THEN 1 ELSE 0 END) as misses,
            SUM(CASE WHEN outcome='pending' THEN 1 ELSE 0 END) as pending,
            AVG(confidence) as avg_confidence
        FROM prediction_records
    ''')
    total, hits, misses, pending, avg_conf = c.fetchone()
    hits = hits or 0
    misses = misses or 0
    pending = pending or 0
    win_rate = (hits / (hits + misses)) if (hits + misses) > 0 else 0
    
    print(f"  Total predictions: {total}")
    print(f"  Hits (wins): {hits}")
    print(f"  Misses (losses): {misses}")
    print(f"  Pending: {pending}")
    print(f"  Win rate: {win_rate:.1%}")
    print(f"  Avg confidence: {avg_conf:.2f}" if avg_conf else "  Avg confidence: N/A")
    
    # Check sport keys
    print("\n🏀 SPORT KEYS IN PREDICTIONS")
    c.execute('SELECT sport_key, COUNT(*) FROM prediction_records GROUP BY sport_key')
    sport_counts = c.fetchall()
    for sport_key, count in sport_counts:
        print(f"  {sport_key or 'NULL'}: {count} predictions")
    
    # By sport breakdown
    print("\n🏀 METRICS BY SPORT")
    c.execute('''
        SELECT 
            sport_key,
            COUNT(*) as total,
            SUM(CASE WHEN outcome='hit' THEN 1 ELSE 0 END) as hits,
            SUM(CASE WHEN outcome='miss' THEN 1 ELSE 0 END) as misses,
            AVG(confidence) as avg_confidence
        FROM prediction_records
        WHERE sport_key IS NOT NULL
        GROUP BY sport_key
    ''')
    
    sport_results = c.fetchall()
    if sport_results:
        for sport_key, total, hits, misses, avg_conf in sport_results:
            hits = hits or 0
            misses = misses or 0
            sport_win_rate = (hits / (hits + misses)) if (hits + misses) > 0 else 0
            print(f"  {sport_key or 'Unknown'}:")
            print(f"    Total: {total}, Hits: {hits}, Misses: {misses}, Win rate: {sport_win_rate:.1%}")
    else:
        print("  No sport breakdown available (all predictions may be club_100_access or have null sport_key)")
    
    # Data integrity check
    print("\n🔍 DATA INTEGRITY CHECK")
    
    # Check for orphaned predictions (no user)
    c.execute('SELECT COUNT(*) FROM prediction_records WHERE user_id IS NULL')
    orphaned = c.fetchone()[0]
    if orphaned > 0:
        print(f"  ⚠️ {orphaned} predictions have no user association")
    else:
        print(f"  ✓ All predictions have user associations")
    
    # Check for users with no predictions
    c.execute('''
        SELECT COUNT(*) FROM users u 
        WHERE NOT EXISTS (SELECT 1 FROM prediction_records p WHERE p.user_id = u.id)
    ''')
    users_no_preds = c.fetchone()[0]
    if users_no_preds > 0:
        print(f"  ℹ️ {users_no_preds} users have no predictions")
    
    print("\n" + "="*70)
    print("✓ VERIFICATION COMPLETE")
    print("="*70 + "\n")
    
    conn.close()
    return {
        'total_predictions': total,
        'hits': hits,
        'misses': misses,
        'pending': pending,
        'users': user_count,
        'win_rate': win_rate
    }

if __name__ == "__main__":
    metrics = verify_database()
