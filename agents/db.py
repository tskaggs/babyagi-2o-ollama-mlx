import sqlite3
from contextlib import contextmanager

DB_PATH = 'babyagi.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Main task and run summary
    c.execute('''CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT,
        manager_subtasks TEXT,
        manager_summary TEXT,
        total_time REAL,
        total_tokens INTEGER,
        user_feedback TEXT,
        model_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    # Agents and their assignments
    c.execute('''CREATE TABLE IF NOT EXISTS agents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER,
        agent_name TEXT,
        assigned_subtask TEXT,
        started_at TIMESTAMP,
        finished_at TIMESTAMP,
        status TEXT,
        exit_reason TEXT,
        config TEXT,
        FOREIGN KEY(run_id) REFERENCES runs(id)
    )''')
    # Agent iterations and responses
    c.execute('''CREATE TABLE IF NOT EXISTS agent_iterations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id INTEGER,
        iteration INTEGER,
        prompt TEXT,
        response TEXT,
        duration REAL,
        tokens_used INTEGER,
        error TEXT,
        tags TEXT,
        parent_iteration_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(agent_id) REFERENCES agents(id)
    )''')
    conn.commit()
    conn.close()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()
