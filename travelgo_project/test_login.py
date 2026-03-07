import sqlite3
import os

# Get the database path
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'travelgo.db')

# Test login logic
email = 'test@example.com'
password = 'password123'

conn = sqlite3.connect(DATABASE)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
user_row = cursor.fetchone()

if user_row:
    user = dict(user_row)
    print(f"User found: {user}")
    print(f"Stored password: {user['password']}")
    print(f"Input password: {password}")
    print(f"Password match: {user['password'] == password}")
else:
    print("User not found")

conn.close()

