import os
import sqlite3

DB_PATH = "memory/memory.db"


def initialize_database():

    os.makedirs(
        "memory",
        exist_ok=True,
    )

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    # ==================================================
    # Users
    # ==================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # ==================================================
    # Trip History
    # ==================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS trip_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            destination TEXT,
            budget INTEGER,
            duration INTEGER,
            travel_style TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # ==================================================
    # Long-Term Memory
    # ==================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS long_term_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            memory_text TEXT NOT NULL,
            memory_type TEXT DEFAULT 'preference',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # ==================================================
    # Chat History
    # ==================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()

    conn.close()