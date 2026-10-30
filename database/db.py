import sqlite3
from pathlib import Path
from utils.config import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'started',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS topic_explanations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                explanation TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (session_id) REFERENCES learning_sessions(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                scenario_title TEXT NOT NULL,
                scenario_description TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (session_id) REFERENCES learning_sessions(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS student_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                answer_text TEXT NOT NULL,
                submitted_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (session_id) REFERENCES learning_sessions(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                total_score INTEGER NOT NULL,
                technical_score INTEGER NOT NULL,
                conceptual_score INTEGER NOT NULL,
                practical_score INTEGER NOT NULL,
                strengths TEXT,
                weaknesses TEXT,
                missing_concepts TEXT,
                corrected_explanation TEXT,
                suggested_answer TEXT,
                recommendations TEXT,
                evaluated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (session_id) REFERENCES learning_sessions(id)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
