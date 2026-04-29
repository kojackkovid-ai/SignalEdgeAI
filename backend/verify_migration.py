import sqlite3
conn = sqlite3.connect('sports_predictions.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM prediction_records')
print('prediction_records:', c.fetchone()[0])
c.execute('SELECT outcome, COUNT(*) FROM prediction_records GROUP BY outcome')
print('by outcome:')
for row in c.fetchall():
    print(row)
conn.close()