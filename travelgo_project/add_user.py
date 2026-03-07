import sqlite3

# Connect to the database
conn = sqlite3.connect('c:/Users/ashwi/OneDrive/Documents/travelgo_project/instance/travelgo.db')
cursor = conn.cursor()

# Insert a test user
cursor.execute("INSERT INTO users (email, name, password, logins) VALUES (?, ?, ?, ?)",
               ('test@example.com', 'Test User', 'password123', 0))

conn.commit()
conn.close()

print("Test user created successfully!")
print("Email: test@example.com")
print("Password: password123")

