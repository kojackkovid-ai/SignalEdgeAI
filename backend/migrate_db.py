import sqlite3
import os

db_path = "sports_predictions.db"
# path might be in backend folder or root. Code says "./sports_predictions.db" relative to execution.
# Assuming we run from project root, it might be in backend/ or root.
# Let's try to find it.

def migrate():
    # Try absolute path first if we know it, otherwise relative
    paths = [
        "c:\\Users\\bigba\\Desktop\\New folder\\sports-prediction-platform\\backend\\sports_predictions.db",
        "c:\\Users\\bigba\\Desktop\\New folder\\sports-prediction-platform\\sports_predictions.db"
    ]
    
    conn = None
    target_path = None
    
    for path in paths:
        if os.path.exists(path):
            target_path = path
            break
            
    if not target_path:
        print("Database file not found. Creating new one or assuming it will be created by app.")
        return

    print(f"Migrating database at {target_path}")
    conn = sqlite3.connect(target_path)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(user_predictions)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'created_at' not in columns:
            print("Adding created_at column to user_predictions...")
            cursor.execute("ALTER TABLE user_predictions ADD COLUMN created_at DATETIME")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column created_at already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
