import sqlite3
from datetime import datetime

DATABASE = "ai_automation.db"


def get_connection():
    return sqlite3.connect(DATABASE)




def _has_unique_constraint(cursor, table, expected_columns):
    indexes = cursor.execute(
        f"PRAGMA index_list({table})"
    ).fetchall()

    for index in indexes:
        if index[2]:  # Unique index
            columns = [
                row[2]
                for row in cursor.execute(
                    f"PRAGMA index_info('{index[1]}')"
                ).fetchall()
            ]

            if columns == expected_columns:
                return True

    return False


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT,
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
                client_id TEXT,
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
                client_id TEXT,
                message_id TEXT UNIQUE,
                processed_at TEXT
            )
        """)

        # Add tenant IDs to existing tables.
        for table in (
            "conversations",
            "escalations",
            "processed_messages",
        ):
            columns = {
                row[1]
                for row in cursor.execute(
                    f"PRAGMA table_info({table})"
                ).fetchall()
            }

            if "client_id" not in columns:
                cursor.execute(
                    f"ALTER TABLE {table} ADD COLUMN client_id TEXT"
                )

            cursor.execute(
                f"UPDATE {table} "
                "SET client_id = 'demo_client' "
                "WHERE client_id IS NULL"
            )

        # Repair processed_messages tenant uniqueness.
        if not _has_unique_constraint(
            cursor,
            "processed_messages",
            ["client_id", "message_id"],
        ):
            cursor.execute("""
                CREATE TABLE processed_messages_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id TEXT,
                    message_id TEXT,
                    processed_at TEXT,
                    UNIQUE(client_id, message_id)
                )
            """)

            cursor.execute("""
                INSERT INTO processed_messages_new (
                    id, client_id, message_id, processed_at
                )
                SELECT
                    id, client_id, message_id, processed_at
                FROM processed_messages
            """)

            cursor.execute("DROP TABLE processed_messages")
            cursor.execute("""
                ALTER TABLE processed_messages_new
                RENAME TO processed_messages
            """)

        # Create memory table for new installations.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customer_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                customer_id TEXT NOT NULL,
                memory_key TEXT NOT NULL,
                memory_value TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(client_id, customer_id, memory_key)
            )
        """)

        memory_columns = {
            row[1]
            for row in cursor.execute(
                "PRAGMA table_info(customer_memory)"
            ).fetchall()
        }

        memory_constraint_ok = (
            _has_unique_constraint(
                cursor,
                "customer_memory",
                ["client_id", "customer_id", "memory_key"],
            )
            and "client_id" in memory_columns
        )

        # Rebuild if the tenant column or composite constraint is missing.
        if not memory_constraint_ok:
            if "client_id" in memory_columns:
                client_expression = (
                    "COALESCE(client_id, 'demo_client')"
                )
            else:
                client_expression = "'demo_client'"

            cursor.execute("DROP TABLE IF EXISTS customer_memory_new")

            cursor.execute("""
                CREATE TABLE customer_memory_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    memory_key TEXT NOT NULL,
                    memory_value TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(client_id, customer_id, memory_key)
                )
            """)

            cursor.execute(f"""
                INSERT INTO customer_memory_new (
                    id, client_id, customer_id, memory_key,
                    memory_value, created_at, updated_at
                )
                SELECT
                    id, {client_expression}, customer_id, memory_key,
                    memory_value, created_at, updated_at
                FROM customer_memory
            """)

            cursor.execute("DROP TABLE customer_memory")
            cursor.execute("""
                ALTER TABLE customer_memory_new
                RENAME TO customer_memory
            """)

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

# =============================================================
# CONVERSATIONS
# =============================================================

def save_conversation(result):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO conversations (
            client_id,
            customer_id,
            message_id,
            timestamp,
            customer_message,
            category,
            ai_response,
            needs_human,
            action
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        result["client_id"],
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


def get_conversation_history(
    client_id,
    customer_id,
    limit=10
):

    if not client_id or not customer_id:
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
        WHERE client_id = ?
        AND customer_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (
        client_id,
        customer_id,
        limit
    ))

    rows = cursor.fetchall()

    connection.close()

    return rows


# =============================================================
# CUSTOMER MEMORY
# =============================================================

def save_customer_memory(
    client_id,
    customer_id,
    memory_key,
    memory_value
):

    if not client_id:
        return

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
            client_id,
            customer_id,
            memory_key,
            memory_value,
            created_at,
            updated_at
        )

        VALUES (?, ?, ?, ?, ?, ?)

        ON CONFLICT(client_id, customer_id, memory_key)
        DO UPDATE SET
            memory_value = excluded.memory_value,
            updated_at = excluded.updated_at
    """, (
        client_id,
        customer_id,
        memory_key,
        memory_value,
        now,
        now
    ))

    connection.commit()
    connection.close()


def get_customer_memory(
    client_id,
    customer_id
):

    if not client_id or not customer_id:
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
        WHERE client_id = ?
        AND customer_id = ?
        ORDER BY id ASC
    """, (
        client_id,
        customer_id
    ))

    rows = cursor.fetchall()

    connection.close()

    return rows


def get_customer_memory_value(
    client_id,
    customer_id,
    memory_key
):

    if (
        not client_id
        or not customer_id
        or not memory_key
    ):
        return None

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT memory_value
        FROM customer_memory
        WHERE client_id = ?
        AND customer_id = ?
        AND memory_key = ?
    """, (
        client_id,
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
            client_id,
            customer_id,
            message_id,
            request_id,
            timestamp,
            category,
            customer_message,
            reason,
            status
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        escalation["client_id"],
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


def get_pending_escalations(client_id):

    if not client_id:
        return []

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
        WHERE client_id = ?
        AND status = 'Pending human review'
        ORDER BY id DESC
    """, (client_id,))

    rows = cursor.fetchall()

    connection.close()

    return rows


def resolve_escalation(
    escalation_id,
    client_id
):

    if not client_id:
        return

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE escalations
        SET status = 'Resolved'
        WHERE id = ?
        AND client_id = ?
    """, (
        escalation_id,
        client_id
    ))

    connection.commit()
    connection.close()


# =============================================================
# PROCESSED MESSAGES
# =============================================================

def is_message_processed(
    client_id,
    message_id
):

    if not client_id or not message_id:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT 1
        FROM processed_messages
        WHERE client_id = ?
        AND message_id = ?
    """, (
        client_id,
        message_id
    ))

    result = cursor.fetchone()

    connection.close()

    return result is not None


def mark_message_processed(
    client_id,
    message_id
):

    if not client_id or not message_id:
        return

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO processed_messages (
                client_id,
                message_id,
                processed_at
            )

            VALUES (?, ?, ?)
        """, (
            client_id,
            message_id,
            datetime.now().isoformat()
        ))

        connection.commit()

    except sqlite3.IntegrityError:

        connection.rollback()

    finally:

        connection.close()