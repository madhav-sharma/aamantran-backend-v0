import sqlite3
from typing import Optional

DB_PATH = "wedding.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
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
        sent BOOLEAN DEFAULT FALSE,
        delivered BOOLEAN DEFAULT FALSE,
        responded_with_button BOOLEAN DEFAULT FALSE,
        message_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_group_id ON guests(group_id);''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_message_id ON guests(message_id);''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guest_id INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        type TEXT NOT NULL,
        payload TEXT NOT NULL,
        status TEXT,
        is_multiple BOOLEAN DEFAULT FALSE
    );
    ''')
    conn.commit()
    conn.close()

# Optional: call init_db() on import
init_db()
