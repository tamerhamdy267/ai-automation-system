import sqlite3
from datetime import datetime

DATABASE = "ai_automation.db"


def get_connection():
    return sqlite3.connect(DATABASE)


def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            customer_id TEXT,

            message_id TEXT,

            timestamp TEXT,

            customer_message TEXT,

            category TEXT,

            ai_response TEXT,

            needs_human INTEGER,

            action TEXT

        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escalations (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            customer_id TEXT,

            message_id TEXT,

            request_id TEXT,

            timestamp TEXT,

            category TEXT,

            customer_message TEXT,

            reason TEXT,

            status TEXT

        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_messages (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            message_id TEXT UNIQUE,

            processed_at TEXT

        )
    """)

    # ---------------------------------------------------------
    # CUSTOMER MEMORY
    #
    # Each customer's memories are isolated by customer_id.
    # ---------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_memory (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            customer_id TEXT NOT NULL,

            memory_key TEXT NOT NULL,

            memory_value TEXT NOT NULL,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            UNIQUE(customer_id, memory_key)

        )
    """)

    connection.commit()
    connection.close()


def save_conversation(result):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO conversations (
            customer_id,
            message_id,
            timestamp,
            customer_message,
            category,
            ai_response,
            needs_human,
            action
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        result["customer_id"],
        result["message_id"],
        result["timestamp"],
        result["text"],
        result["category"],
        result["response"]["response"],
        int(result["needs_human"]),
        result["action"]
    ))

    connection.commit()
    connection.close()


def get_conversation_history(customer_id, limit=10):

    if not customer_id:
        return []

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            customer_id,
            message_id,
            timestamp,
            customer_message,
            category,
            ai_response,
            needs_human,
            action
        FROM conversations
        WHERE customer_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (customer_id, limit))

    rows = cursor.fetchall()

    connection.close()

    return rows


# =============================================================
# CUSTOMER MEMORY FUNCTIONS
# =============================================================

def save_customer_memory(customer_id, memory_key, memory_value):

    if not customer_id:
        return

    if not memory_key:
        return

    if not memory_value:
        return

    now = datetime.now().isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO customer_memory (
            customer_id,
            memory_key,
            memory_value,
            created_at,
            updated_at
        )

        VALUES (?, ?, ?, ?, ?)

        ON CONFLICT(customer_id, memory_key)
        DO UPDATE SET
            memory_value = excluded.memory_value,
            updated_at = excluded.updated_at
    """, (
        customer_id,
        memory_key,
        memory_value,
        now,
        now
    ))

    connection.commit()
    connection.close()


def get_customer_memory(customer_id):

    if not customer_id:
        return []

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            memory_key,
            memory_value,
            created_at,
            updated_at
        FROM customer_memory
        WHERE customer_id = ?
        ORDER BY id ASC
    """, (customer_id,))

    rows = cursor.fetchall()

    connection.close()

    return rows


def get_customer_memory_value(customer_id, memory_key):

    if not customer_id or not memory_key:
        return None

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT memory_value
        FROM customer_memory
        WHERE customer_id = ?
        AND memory_key = ?
    """, (
        customer_id,
        memory_key
    ))

    row = cursor.fetchone()

    connection.close()

    if row:
        return row[0]

    return None


# =============================================================
# ESCALATIONS
# =============================================================

def save_escalation(escalation):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO escalations (
            customer_id,
            message_id,
            request_id,
            timestamp,
            category,
            customer_message,
            reason,
            status
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        escalation["customer_id"],
        escalation["message_id"],
        escalation["request_id"],
        escalation["timestamp"],
        escalation["category"],
        escalation["customer_message"],
        escalation["reason"],
        escalation["status"]
    ))

    connection.commit()
    connection.close()


def get_pending_escalations():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            customer_id,
            message_id,
            category,
            customer_message,
            reason,
            status
        FROM escalations
        WHERE status = 'Pending human review'
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    connection.close()

    return rows


def resolve_escalation(escalation_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE escalations
        SET status = 'Resolved'
        WHERE id = ?
    """, (escalation_id,))

    connection.commit()
    connection.close()


# =============================================================
# PROCESSED MESSAGES
# =============================================================

def is_message_processed(message_id):

    if not message_id:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT 1
        FROM processed_messages
        WHERE message_id = ?
    """, (message_id,))

    result = cursor.fetchone()

    connection.close()

    return result is not None


def mark_message_processed(message_id):

    if not message_id:
        return

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO processed_messages (
                message_id,
                processed_at
            )

            VALUES (?, ?)
        """, (
            message_id,
            datetime.now().isoformat()
        ))

        connection.commit()

    except sqlite3.IntegrityError:

        pass

    finally:

        connection.close()


if __name__ == "__main__":

    initialize_database()

    print("Database initialized successfully.")