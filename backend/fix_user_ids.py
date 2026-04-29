#!/usr/bin/env python3
"""
Fix user ID mismatch in prediction_records
"""
import sqlite3

def fix_user_ids():
    conn = sqlite3.connect('sports_predictions.db')
    c = conn.cursor()
    
    # Get the test user ID
    c.execute('SELECT id FROM users WHERE username = "testuser"')
    user_result = c.fetchone()
    if not user_result:
        print("❌ No testuser found")
        return
    
    correct_user_id = user_result[0]
    print(f"✓ Found testuser with ID: {correct_user_id}")
    
    # Update all prediction_records to use this user_id
    c.execute('UPDATE prediction_records SET user_id = ?', (correct_user_id,))
    updated_count = c.rowcount
    conn.commit()
    
    print(f"✓ Updated {updated_count} prediction records to use user_id: {correct_user_id}")
    
    # Verify the update
    c.execute('SELECT COUNT(*) FROM prediction_records WHERE user_id = ?', (correct_user_id,))
    count = c.fetchone()[0]
    print(f"✓ Verification: {count} predictions now associated with testuser")
    
    conn.close()

if __name__ == "__main__":
    fix_user_ids()