"""
Simple SQLite database layer — no external DB server needed.
Creates mindsense.db (a single file) the first time the app runs.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "mindsense.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            member_since TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS auth_tokens (
            token TEXT PRIMARY KEY,
            patient_id INTEGER NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS health_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            heart_rate REAL,
            sleep_hours REAL,
            study_hours REAL,
            academic_stressors INTEGER,
            mental_health_score REAL,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )
    """)

    conn.commit()
    conn.close()
