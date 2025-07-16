import sqlite3
from contextlib import contextmanager
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

DB_PATH = Path("wedding.db")


def init_database():
    """Initialize the database with required tables"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Create guests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prefix TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                greeting_name TEXT,
                phone TEXT UNIQUE,
                group_id TEXT NOT NULL,
                is_group_primary BOOLEAN NOT NULL,
                ready BOOLEAN NOT NULL DEFAULT FALSE,
                sent_to_whatsapp TEXT DEFAULT 'pending',
                api_call_at DATETIME,
                sent_at DATETIME,
                delivered_at DATETIME,
                read_at DATETIME,
                responded_with_button BOOLEAN DEFAULT FALSE,
                message_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guest_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                type TEXT NOT NULL,
                payload TEXT NOT NULL,
                status TEXT,
                is_multiple BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Create WhatsApp API calls table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS whatsapp_api_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                guest_id INTEGER,
                direction VARCHAR(10) CHECK (direction IN ('request', 'response')),
                method VARCHAR(10),
                url TEXT,
                headers TEXT,
                payload TEXT,
                status_code INTEGER,
                response_time_ms INTEGER,
                error_message TEXT,
                FOREIGN KEY (guest_id) REFERENCES guests(id)
            )
        """)
        
        # Create webhook payloads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS webhook_payloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type VARCHAR(50),
                payload TEXT,
                headers TEXT,
                processed BOOLEAN DEFAULT 0
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_id ON guests(group_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_message_id ON guests(message_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_calls_timestamp ON whatsapp_api_calls(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_calls_guest_id ON whatsapp_api_calls(guest_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_webhooks_timestamp ON webhook_payloads(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_webhooks_event_type ON webhook_payloads(event_type)")
        
        conn.commit()
        logger.info("Database initialized successfully")


@contextmanager
def get_db():
    """Get a database connection context manager"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
    finally:
        conn.close()


def get_db_path():
    """Get the database path as a string"""
    return str(DB_PATH) 