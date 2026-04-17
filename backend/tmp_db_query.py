import sqlite3

conn = sqlite3.connect('sports_predictions.db')
cur = conn.cursor()

# list tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print('tables:', cur.fetchall())

# show users schema
try:
    cur.execute('PRAGMA table_info(users)')
    print('users schema:', cur.fetchall())
except Exception as e:
    print('users table error', e)

# fetch some users
try:
    cur.execute('SELECT id, email, username, subscription_tier FROM users LIMIT 5')
    print('users:', cur.fetchall())
except Exception as e:
    print('select users error', e)

conn.close()
