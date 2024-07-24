import sqlite3
import os
from werkzeug.security import generate_password_hash

def get_db_connection():
    db_path = os.path.abspath('../sales_record.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table with role column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'employee'
        )
    ''')

    # Create sales table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            item TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL
        )
    ''')

    # Create inventory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT UNIQUE NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def set_user_as_admin(username):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Update the user's role to 'admin'
    cursor.execute('''
        UPDATE users 
        SET role = 'admin' 
        WHERE username = ?
    ''', (username,))

    if cursor.rowcount == 0:
        print(f"No user found with username: {username}")
    else:
        print(f"User {username} has been set as admin.")

    conn.commit()
    conn.close()

def create_admin_user(username, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the username or email already exists
    cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
    existing_user = cursor.fetchone()

    if existing_user:
        print("Username or email already exists.")
        conn.close()
        return False

    # Hash the password
    hashed_password = generate_password_hash(password)

    # Insert new admin user
    cursor.execute('''
        INSERT INTO users (username, email, password, role)
        VALUES (?, ?, ?, 'admin')
    ''', (username, email, hashed_password))

    conn.commit()
    conn.close()

    print(f"Admin user {username} created successfully.")
    return True

if __name__ == '__main__':
    create_tables()
    print("Database tables created successfully.")
    
    # Prompt to create a new admin user
    create_new_admin = input("Do you want to create a new admin user? (y/n): ").lower()
    if create_new_admin == 'y':
        username = input("Enter admin username: ")
        email = input("Enter admin email: ")
        password = input("Enter admin password: ")
        if create_admin_user(username, email, password):
            print("New admin user created successfully.")
    else:
        # Prompt to set an existing user as admin
        admin_username = input("Enter the username of an existing user to set as admin (or press Enter to skip): ")
        if admin_username:
            set_user_as_admin(admin_username)