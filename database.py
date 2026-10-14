import sqlite3


DATABASE_NAME = "db.sqlite3"


def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            classification TEXT,
            risk_score REAL,
            confidence REAL,
            scan_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            result_json TEXT
        )
    """)

    connection.commit()
    connection.close()