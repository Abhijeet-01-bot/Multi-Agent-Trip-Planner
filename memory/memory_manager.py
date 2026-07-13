import sqlite3

DB_PATH = "memory/memory.db"


def create_user(user_id: str):

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT OR IGNORE INTO users(user_id)
        VALUES(?)
        """,
        (user_id,),
    )

    conn.commit()
    conn.close()


# ==================================================
# Trip Memory
# ==================================================

def save_trip(
    user_id,
    destination,
    budget,
    duration,
    travel_style,
):

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT INTO trip_history(
            user_id,
            destination,
            budget,
            duration,
            travel_style
        )
        VALUES(?,?,?,?,?)
        """,
        (
            user_id,
            destination,
            budget,
            duration,
            travel_style,
        ),
    )

    conn.commit()
    conn.close()


def get_recent_trips(
    user_id,
    limit=10,
):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.execute(
        """
        SELECT
            destination,
            budget,
            duration,
            travel_style
        FROM trip_history
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            user_id,
            limit,
        ),
    )

    rows = cursor.fetchall()

    conn.close()

    return rows


# ==================================================
# Long-Term Memory
# ==================================================

def save_memory(
    user_id,
    memory_text,
    memory_type="preference",
):

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT INTO long_term_memory(
            user_id,
            memory_text,
            memory_type
        )
        VALUES(?,?,?)
        """,
        (
            user_id,
            memory_text,
            memory_type,
        ),
    )

    conn.commit()
    conn.close()


def get_memories(
    user_id,
    limit=20,
):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.execute(
        """
        SELECT memory_text
        FROM long_term_memory
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            user_id,
            limit,
        ),
    )

    rows = cursor.fetchall()

    conn.close()

    return [row[0] for row in rows]


# ==================================================
# Chat History
# ==================================================

def save_chat_message(
    user_id,
    role,
    message,
):

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT INTO chat_history(
            user_id,
            role,
            message
        )
        VALUES(?,?,?)
        """,
        (
            user_id,
            role,
            message,
        ),
    )

    conn.commit()
    conn.close()


def get_chat_history(
    user_id,
    limit=100,
):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.execute(
        """
        SELECT
            role,
            message
        FROM chat_history
        WHERE user_id = ?
        ORDER BY id ASC
        LIMIT ?
        """,
        (
            user_id,
            limit,
        ),
    )

    rows = cursor.fetchall()

    conn.close()

    return rows


# ==================================================
# Full User Memory Snapshot
# ==================================================

def get_user_memory_snapshot(user_id):

    return {
        "previous_trips": get_recent_trips(user_id),
        "retrieved_memories": get_memories(user_id),
        "chat_history": get_chat_history(user_id),
    }