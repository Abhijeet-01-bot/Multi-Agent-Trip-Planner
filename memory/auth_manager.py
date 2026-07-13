import sqlite3
import hashlib

DB_PATH = "memory/memory.db"


def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()


def initialize_auth_table():
    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS auth_users (
            user_id TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()


def register_user(user_id, password):
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.execute(
        """
        SELECT user_id
        FROM auth_users
        WHERE user_id=?
        """,
        (user_id,),
    )

    existing = cursor.fetchone()

    if existing:
        conn.close()
        return False

    conn.execute(
        """
        INSERT INTO auth_users(
            user_id,
            password_hash
        )
        VALUES (?,?)
        """,
        (
            user_id,
            hash_password(password),
        ),
    )

    conn.commit()
    conn.close()

    return True


def authenticate_user(
    user_id,
    password,
):
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.execute(
        """
        SELECT password_hash
        FROM auth_users
        WHERE user_id=?
        """,
        (user_id,),
    )

    row = cursor.fetchone()

    conn.close()

    if not row:
        return False

    stored_hash = row[0]

    return (
        stored_hash
        == hash_password(password)
    )
