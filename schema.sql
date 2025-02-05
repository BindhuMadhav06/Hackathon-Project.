-- Create the 'users' table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Auto-incrementing user ID
    username TEXT NOT NULL UNIQUE,         -- Username (unique)
    email TEXT NOT NULL UNIQUE,            -- Email (unique)
    password TEXT NOT NULL                 -- Hashed password
);

-- Create the 'passwords' table
CREATE TABLE IF NOT EXISTS passwords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Auto-incrementing password ID
    user_id INTEGER NOT NULL,              -- User ID (foreign key)
    website TEXT NOT NULL,                 -- Website where the password is used
    username TEXT NOT NULL,                -- Username for the website
    password TEXT NOT NULL,                -- Hashed password for the website
    FOREIGN KEY(user_id) REFERENCES users(id)  -- Link to the 'users' table
);
