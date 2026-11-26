"""
database/db_manager.py
Database layer for AI Finance Tracker:
- Multi-user authentication (Registration, Secure SHA-256 Passwords with Salt, Login)
- User-isolated Transaction CRUD operations
- Bulk statement import with duplicate avoidance
- Backward-compatible schema migration (adds user_id column and users table)
"""

import sqlite3
import hashlib
import os
import pandas as pd

DB_FILE = "finance.db"


def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Generates salt and SHA-256 salted password hash."""
    if salt is None:
        salt = os.urandom(16).hex()
    salted = f"{salt}{password}".encode("utf-8")
    pwd_hash = hashlib.sha256(salted).hexdigest()
    return pwd_hash, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verifies candidate password against stored hash."""
    candidate_hash, _ = hash_password(password, salt)
    return candidate_hash == stored_hash


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Transactions Table with user_id
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            type TEXT NOT NULL,
            note TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # 3. Migration check: if transactions table existed without user_id column
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [col[1] for col in cursor.fetchall()]
    if "user_id" not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER DEFAULT 1")

    conn.commit()
    conn.close()


# ----------------- AUTHENTICATION HELPERS -----------------

def register_user(username: str, name: str, password: str) -> tuple[bool, str, int | None]:
    """Registers a new user. Returns (success, message, user_id)."""
    username = username.strip().lower()
    name = name.strip()
    if not username or not password or not name:
        return False, "All fields are required.", None
    if len(password) < 4:
        return False, "Password must be at least 4 characters long.", None

    conn = get_connection()
    cursor = conn.cursor()
    try:
        pwd_hash, salt = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, name, password_hash, salt) VALUES (?, ?, ?, ?)",
            (username, name, pwd_hash, salt),
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return True, "Registration successful!", user_id
    except sqlite3.IntegrityError:
        conn.close()
        return False, f"Username '{username}' already exists. Please choose another.", None
    except Exception as e:
        conn.close()
        return False, f"Registration error: {e}", None


def authenticate_user(username: str, password: str) -> tuple[bool, str, dict | None]:
    """Authenticates user. Returns (success, message, user_dict)."""
    username = username.strip().lower()
    if not username or not password:
        return False, "Please enter both username and password.", None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, name, password_hash, salt FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False, "Invalid username or password.", None

    user_id, u_name, full_name, stored_hash, salt = row
    if verify_password(password, stored_hash, salt):
        return True, "Login successful!", {
            "id": user_id,
            "username": u_name,
            "name": full_name,
        }
    return False, "Invalid username or password.", None


# ----------------- USER-ISOLATED TRANSACTION CRUD -----------------

def add_transaction(date, amount, category, tx_type, note, user_id=1):
    """Inserts a single transaction tied to a specific user_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO transactions(date, amount, category, type, note, user_id) VALUES(?,?,?,?,?,?)""",
        (str(date), float(amount), category, tx_type, note, user_id),
    )
    conn.commit()
    conn.close()


def bulk_insert_transactions(records: list[dict], user_id: int, skip_duplicates: bool = True) -> tuple[int, int]:
    """
    Inserts a batch of parsed transactions for a user.
    Returns (inserted_count, skipped_count).
    """
    if not records:
        return 0, 0

    conn = get_connection()
    cursor = conn.cursor()

    existing_set = set()
    if skip_duplicates:
        cursor.execute("SELECT date, amount, type, note FROM transactions WHERE user_id = ?", (user_id,))
        for r in cursor.fetchall():
            # normalize for fuzzy duplicate match
            d, a, t, n = r
            existing_set.add((str(d).strip(), float(a), str(t).strip(), str(n or "").strip().lower()))

    to_insert = []
    skipped = 0

    for item in records:
        key = (
            str(item["date"]).strip(),
            float(item["amount"]),
            str(item["type"]).strip(),
            str(item.get("note", "") or "").strip().lower(),
        )
        if skip_duplicates and key in existing_set:
            skipped += 1
            continue

        to_insert.append((
            str(item["date"]),
            float(item["amount"]),
            str(item["category"]),
            str(item["type"]),
            str(item.get("note", "")),
            int(user_id),
        ))
        existing_set.add(key)

    if to_insert:
        cursor.executemany(
            """INSERT INTO transactions(date, amount, category, type, note, user_id) VALUES (?,?,?,?,?,?)""",
            to_insert,
        )
        conn.commit()

    conn.close()
    return len(to_insert), skipped


def load_transactions_df(user_id=None):
    """Loads transactions. If user_id is given, filters strictly by that user."""
    conn = get_connection()
    if user_id is not None:
        query = "SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC"
        df = pd.read_sql_query(query, conn, params=(user_id,))
    else:
        df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()
    return df


def delete_transaction(transaction_id, user_id=None):
    """Deletes transaction with optional user_id guardrail."""
    conn = get_connection()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (transaction_id, user_id))
    else:
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()


def update_transaction(id, date, amount, category, tx_type, note, user_id=None):
    """Updates transaction with optional user_id guardrail."""
    conn = get_connection()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute(
            """UPDATE transactions SET date=?, amount=?, category=?, type=?, note=? WHERE id=? AND user_id=?""",
            (str(date), float(amount), category, tx_type, note, id, user_id),
        )
    else:
        cursor.execute(
            """UPDATE transactions SET date=?, amount=?, category=?, type=?, note=? WHERE id=?""",
            (str(date), float(amount), category, tx_type, note, id),
        )
    conn.commit()
    conn.close()


def preload_seed_data(default_user_id=1):
    """Creates a default demo user and loads seed transactions if DB is empty."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if demo user exists
    cursor.execute("SELECT id FROM users WHERE username = 'aditya'")
    demo_user = cursor.fetchone()
    if not demo_user:
        pwd_hash, salt = hash_password("demo123")
        cursor.execute(
            "INSERT INTO users (id, username, name, password_hash, salt) VALUES (?, ?, ?, ?, ?)",
            (1, "aditya", "Aditya Prakash", pwd_hash, salt),
        )
        conn.commit()
        demo_user_id = 1
    else:
        demo_user_id = demo_user[0]

    cursor.execute("SELECT COUNT(*) FROM transactions")
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0:
        try:
            seed_df = pd.read_csv("data/seed_transactions.csv")
            for _, row in seed_df.iterrows():
                add_transaction(
                    row["date"],
                    row["amount"],
                    row["category"],
                    row["type"],
                    row["note"],
                    user_id=demo_user_id,
                )
            print(f"Loaded {len(seed_df)} seed transactions for user #{demo_user_id}")
        except FileNotFoundError:
            print("Seed file not found. Starting with empty transactions.")
    else:
        # Update any legacy NULL user_id rows to demo_user_id
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE transactions SET user_id = ? WHERE user_id IS NULL", (demo_user_id,))
        conn.commit()
        conn.close()
