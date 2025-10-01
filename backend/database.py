import sqlite3
import os

DB_NAME = "expenses.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    """Create the expenses table if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            main_category TEXT NOT NULL,
            mid_category TEXT,
            sub_category TEXT,
            date TEXT NOT NULL,
            value REAL NOT NULL,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()
