import sqlite3
conn = sqlite3.connect('sports_predictions.db')
c = conn.cursor()

# Check users
c.execute('SELECT COUNT(*) FROM users')
user_count = c.fetchone()[0]
print(f'Users: {user_count}')

if user_count > 0:
    c.execute('SELECT id, username, win_rate, total_predictions, roi FROM users LIMIT 5')
    users = c.fetchall()
    print('User stats:')
    for u in users:
        print(f'  {u[1]}: {u[3]} predictions, {u[2]:.1%} win rate, {u[3]:.1f}% ROI')

# Check prediction records
c.execute('SELECT user_id, COUNT(*) FROM prediction_records GROUP BY user_id')
user_predictions = c.fetchall()
print('Predictions by user:')
for up in user_predictions:
    print(f'  User {up[0]}: {up[1]} predictions')

conn.close()