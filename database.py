import sqlite3
import json
import hashlib
from datetime import datetime

# ---------------------------
# 🔌 Database Connection Setup
# ---------------------------
conn = sqlite3.connect('data.db', check_same_thread=False)
c = conn.cursor()


# ---------------------------
# 🧱 Initialize Database Tables
# ---------------------------
def init_db():
    """Create necessary tables if they don't exist."""
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            name TEXT,
            age INTEGER,
            dob TEXT,
            gender TEXT,
            address TEXT,
            email TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS product_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            product TEXT,
            confidence REAL,
            timestamp TEXT,
            image BLOB,
            results TEXT
        )
    """)

    conn.commit()


# ---------------------------
# 🧩 Compatibility (old imports)
# ---------------------------
def create_usertable():
    """Old compatibility helper — ensures users table exists."""
    init_db()


def ensure_db_ready():
    """Ensure DB initialized on import."""
    try:
        init_db()
    except Exception as e:
        print(f"[DB ERROR] Initialization failed: {e}")


# ---------------------------
# 💾 Product History Functions
# ---------------------------
def add_to_history(username, product, confidence, image_bytes, results):
    """Add analyzed product details to history."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO product_history (username, product, confidence, timestamp, image, results)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (username, product, confidence, timestamp, image_bytes, json.dumps(results)))
    conn.commit()


def get_user_history(username):
    """Fetch product history for the given username."""
    c.execute('''
        SELECT id, product, confidence, timestamp, image, results
        FROM product_history
        WHERE username = ?
        ORDER BY id DESC
    ''', (username,))
    rows = c.fetchall()
    history = []
    for row in rows:
        try:
            results = json.loads(row[5]) if row[5] else []
        except json.JSONDecodeError:
            results = []
        history.append({
            'id': row[0],
            'product': row[1],
            'confidence': row[2],
            'timestamp': row[3],
            'image': row[4],
            'results': results
        })
    return history


def delete_history_item(item_id, username):
    """Delete a specific product from user's history."""
    c.execute('DELETE FROM product_history WHERE id = ? AND username = ?', (item_id, username))
    conn.commit()


def clear_user_history(username):
    """Delete all product history entries for a specific user."""
    c.execute('DELETE FROM product_history WHERE username = ?', (username,))
    conn.commit()


# ---------------------------
# 🔐 User Management Functions
# ---------------------------
def make_hash(password):
    """Generate SHA256 hash for passwords."""
    return hashlib.sha256(str.encode(password)).hexdigest()


def check_hash(password, hashed_text):
    """Check if a given password matches the hash."""
    return make_hash(password) == hashed_text


def add_userdata(username, password, name, age, dob, gender, address, email):
    """Add a new user to the database."""
    try:
        c.execute('''
            INSERT INTO users (username, password, name, age, dob, gender, address, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, password, name, age, dob, gender, address, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def login_user(username, hashed_password):
    """Validate user login."""
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_password))
    return c.fetchone()


def reset_password(username, new_hashed_password):
    """Reset password for a user."""
    c.execute('UPDATE users SET password = ? WHERE username = ?', (new_hashed_password, username))
    conn.commit()
    return c.rowcount > 0


def user_exists(username):
    """Check if a username already exists."""
    c.execute('SELECT 1 FROM users WHERE username = ?', (username,))
    return c.fetchone() is not None


def get_user_data(username):
    """Retrieve user details for profile display."""
    c.execute('SELECT username, name, age, dob, gender, address, email FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    if row:
        return {
            'username': row[0],
            'name': row[1],
            'age': row[2],
            'dob': row[3],
            'gender': row[4],
            'address': row[5],
            'email': row[6],
        }
    return None


def update_user_data(username, name, age, dob, gender, address, email):
    """Update profile information for a given user."""
    c.execute('''
        UPDATE users
        SET name = ?, age = ?, dob = ?, gender = ?, address = ?, email = ?
        WHERE username = ?
    ''', (name, age, dob, gender, address, email, username))
    conn.commit()
    return c.rowcount > 0


# ---------------------------
# 🚀 Initialize on Import
# ---------------------------
ensure_db_ready()