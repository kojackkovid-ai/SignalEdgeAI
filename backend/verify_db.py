import sqlite3
import os

# Try to find the db file again
paths = [
    "c:\\Users\\bigba\\Desktop\\New folder\\sports-prediction-platform\\backend\\sports_predictions.db",
    "c:\\Users\\bigba\\Desktop\\New folder\\sports-prediction-platform\\sports_predictions.db"
]

target_path = None
for path in paths:
    if os.path.exists(path):
        target_path = path
        break

if target_path:
    print(f"Checking DB at: {target_path}")
    conn = sqlite3.connect(target_path)
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(user_predictions)")
        columns = [info[1] for info in cursor.fetchall()]
        print(f"Columns in user_predictions: {columns}")
        if 'created_at' in columns:
            print("VERIFICATION SUCCESS: created_at column exists.")
        else:
            print("VERIFICATION FAILED: created_at column missing.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
else:
    print("Database file not found.")
