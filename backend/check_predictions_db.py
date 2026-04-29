import sqlite3
import os

p = 'predictions.db'
print('path', os.path.abspath(p))
print('exists', os.path.exists(p), 'size', os.path.getsize(p) if os.path.exists(p) else None)
conn = sqlite3.connect(p)
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('tables', c.fetchall())
try:
    c.execute("PRAGMA table_info(predictions)")
    print('predictions columns', c.fetchall())
except Exception as e:
    print('predictions pragma error', e)
try:
    c.execute("SELECT COUNT(*) FROM predictions")
    print('count', c.fetchone()[0])
except Exception as e:
    print('select count error', e)
conn.close()
