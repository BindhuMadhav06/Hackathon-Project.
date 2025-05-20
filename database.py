import sqlite3

DATABASE = 'passwords.db'

# Function to get the database connection
def get_db():
    """Connect to the database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Allows column access by name
    return conn

# Function to close the database connection ✅
def close_db(conn):
    """Close the database connection."""
    if conn is not None:
        conn.close()

def get_password(website):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT website, username, password FROM passwords WHERE website = ?", (website,))
        password_entry = cursor.fetchone()
        if password_entry:
            return {
                'website': password_entry[0],
                'username': password_entry[1],
                'password': password_entry[2]
            }
        return None
    finally:
        cursor.close()
        close_db(db)


# Function to initialize the database
def init_db():
    """Create necessary tables in the database."""
    db = get_db()
    cursor = db.cursor()

    # Create users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        email TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL
                    )''')

    # Create passwords table
    cursor.execute('''CREATE TABLE IF NOT EXISTS passwords (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        website TEXT NOT NULL,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                    )''')

    db.commit()
    close_db(db)  # ✅ Properly close the database
    print("✅ Database initialized successfully!")

# Run initialization if this file is executed directly
if __name__ == "__main__":
    init_db()
