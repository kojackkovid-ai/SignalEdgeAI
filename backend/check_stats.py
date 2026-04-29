import sqlite3
conn = sqlite3.connect('sports_predictions.db')
c = conn.cursor()

c.execute('SELECT username, total_predictions, win_rate, roi FROM users')
users = c.fetchall()
print('Users:')
for u in users:
    print(f'  {u[0]}: {u[1]} predictions, {u[2]:.1%} win rate, {u[3]:.1f}% ROI')

conn.close()