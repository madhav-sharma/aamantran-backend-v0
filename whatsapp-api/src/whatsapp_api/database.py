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
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                greeting_name TEXT,
                phone TEXT,
                group_id TEXT NOT NULL,
                is_group_primary BOOLEAN NOT NULL,
                ready BOOLEAN NOT NULL DEFAULT FALSE,
                sent_to_whatsapp TEXT DEFAULT 'pending',
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
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_id ON guests(group_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_message_id ON guests(message_id)")
        
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