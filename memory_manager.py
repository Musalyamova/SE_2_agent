import sqlite3
from datetime import datetime

DB_PATH = "long_term_memory.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT,
            content TEXT,
            status TEXT DEFAULT 'confirmed',
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    conn.commit()
    conn.close()


def save_fact(kind: str, content: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO facts (kind, content, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (kind, content, 'confirmed', now, now)
    )
    conn.commit()
    conn.close()
    return f"Факт сохранен: {content}"

def get_project_rules() -> str:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM facts WHERE kind = 'project_rule' AND status = 'confirmed'")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "Правил пока нет"
    return "\n".join([f"- {row[0]}" for row in rows])

def remember_project_rule(rule: str) -> str:
    """Сохраняет правило проекта в долгосрочную память."""
    return save_fact("project_rule", rule)


def learn_new_fact(rule: str):
    """Сохраняет новое абстрактное правило безопасности в долгосрочную память."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM facts WHERE content = ?", (rule,))
    if cursor.fetchone():
        conn.close()
        return "Правило уже известно"

    now = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO facts (kind, content, status, created_at, updated_at) VALUES ('learned_rule', ?, 'confirmed', ?, ?)",
        (rule, now, now)
    )
    conn.commit()
    conn.close()
    return f"Новое правило сохранено: {rule}"