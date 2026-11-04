
import sqlite3

DB_NAME = "learnlyt.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Subjects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    # Topics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            name TEXT NOT NULL,
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        )
    """)

    # Quiz questions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
    """)

    # Quiz results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER,
            score REAL DEFAULT 0,
            correct_answers INTEGER DEFAULT 0,
            total_questions INTEGER DEFAULT 0,
            date TEXT,
            FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
    """)

    # Revision schedule table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS revision_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER,
            next_revision TEXT,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
    """)

    # Automatically update older quiz_results tables
    cursor.execute("PRAGMA table_info(quiz_results)")
    columns = [row["name"] for row in cursor.fetchall()]

    if "correct_answers" not in columns:
        cursor.execute("""
            ALTER TABLE quiz_results
            ADD COLUMN correct_answers INTEGER DEFAULT 0
        """)

    if "total_questions" not in columns:
        cursor.execute("""
            ALTER TABLE quiz_results
            ADD COLUMN total_questions INTEGER DEFAULT 0
        """)

    if "date" not in columns:
        cursor.execute("""
            ALTER TABLE quiz_results
            ADD COLUMN date TEXT
        """)

    conn.commit()
    conn.close()
