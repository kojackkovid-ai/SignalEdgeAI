"""
Phase 5: Database Migration - Add Outcome Tracking Columns
Adds resolved_at, result, and actual_value columns to prediction table
"""

import sqlite3
from pathlib import Path
import sys

DB_PATH = Path(__file__).parent / "backend" / "sports.db"

def add_columns_if_missing():
    """Add outcome tracking columns to prediction table"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(prediction)")
        columns = {row[1] for row in cursor.fetchall()}
        
        migrations = {
            'resolved_at': 'DATETIME DEFAULT NULL',
            'result': 'BOOLEAN DEFAULT NULL',
            'actual_value': 'FLOAT DEFAULT NULL'
        }
        
        added_columns = []
        for col_name, col_def in migrations.items():
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE prediction ADD COLUMN {col_name} {col_def}")
                    added_columns.append(col_name)
                    print(f"✓ Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"  Column {col_name} already exists")
                    else:
                        raise
        
        conn.commit()
        conn.close()
        
        if added_columns:
            print(f"\n✓ Successfully added {len(added_columns)} columns to prediction table")
            return True
        else:
            print(f"\n✓ All required columns already exist")
            return True
    
    except sqlite3.DatabaseError as e:
        print(f"✗ Database error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Run database migration"""
    print("="*60)
    print("PHASE 5: DATABASE MIGRATION")
    print("="*60)
    
    if not DB_PATH.exists():
        print(f"\n✗ Database not found: {DB_PATH}")
        print("  Create database first: python backend/init_db.py")
        return 1
    
    print(f"\nTarget database: {DB_PATH}")
    print("\n[1/1] Adding outcome tracking columns...")
    
    if add_columns_if_missing():
        print("\n✓ Migration complete!")
        return 0
    else:
        print("\n✗ Migration failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
