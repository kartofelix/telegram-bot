import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect("analytics.db", check_same_thread=False)
cursor = conn.cursor()

# ================== TABLES ==================

cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    user_id INTEGER,
    username TEXT,
    event_type TEXT,
    created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS reputation (
    chat_id INTEGER,
    from_user INTEGER,
    to_user INTEGER,
    value INTEGER,
    created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS achievements (
    chat_id INTEGER,
    user_id INTEGER,
    name TEXT,
    created_at TEXT,
    UNIQUE(chat_id, user_id, name)
)
""")

conn.commit()

# 🔹 swear events (матюки)
cursor.execute("""
CREATE TABLE IF NOT EXISTS swear_events (
    chat_id INTEGER,
    user_id INTEGER,
    username TEXT,
    created_at TEXT
)
""")
conn.commit()

# ================== ACHIEVEMENTS ==================

ACHIEVEMENTS = [
    (100,   "Перші кроки Свині"),
    (420,   "Філософ"),
    (500,   "RFL хуйня"),
    (1000,  "Хуєсос"),
    (1161,  "Завоз"),
    (1488,  "Завозік опять"),
    (5000,  "Пиздун"),
    (10000, "Ломка"),
    (15000, "Шизік"),
    (20000, "Йди нахуй"),
    (50000, "Смертоносний"),
]

ACHIEVEMENT_DESCRIPTIONS = {
    100:   "Свиня навчилася писати і не може зупинитись.",
    420:   "Очівка тільки для нашого нацика.",
    500:   "Кейс говно за 500.",
    1000:  "Опис не придумав.",
    1161:  "Нацик таке любить, улюблені його пасхалки.",
    1488:  "Нацик вже кипить від пасхалочки.",
    5000:  "Пиздун і пиздолиз.",
    10000: "Не може перестати писати хуйню.",
    15000: "Завжди у всякій сварці (з мечиком).",
    20000: "Я заїбався писати і думати, стули єбло.",
    50000: "Олд чату або син залупи.",
}

# ================== FUNCTIONS ==================

def log_message(chat_id: int, user_id: int, username: str):
    cursor.execute(
        """
        INSERT INTO events (chat_id, user_id, username, event_type, created_at)
        VALUES (?, ?, ?, 'message', ?)
        """,
        (chat_id, user_id, username, datetime.utcnow().isoformat())
    )
    conn.commit()


def get_message_count(chat_id: int, user_id: int):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM events
        WHERE chat_id = ? AND user_id = ? AND event_type = 'message'
        """,
        (chat_id, user_id)
    )
    return cursor.fetchone()[0]


def has_achievement(chat_id: int, user_id: int, name: str):
    cursor.execute(
        """
        SELECT 1
        FROM achievements
        WHERE chat_id = ? AND user_id = ? AND name = ?
        """,
        (chat_id, user_id, name)
    )
    return cursor.fetchone() is not None


def add_achievement(chat_id: int, user_id: int, name: str):
    cursor.execute(
        """
        INSERT OR IGNORE INTO achievements
        (chat_id, user_id, name, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (chat_id, user_id, name, datetime.utcnow().isoformat())
    )
    conn.commit()


def can_give_rep(chat_id: int, from_user: int, to_user: int):
    today = datetime.utcnow().date().isoformat()
    cursor.execute(
        """
        SELECT 1 FROM reputation
        WHERE chat_id = ?
          AND from_user = ?
          AND to_user = ?
          AND DATE(created_at) = ?
        """,
        (chat_id, from_user, to_user, today)
    )
    return cursor.fetchone() is None


def add_rep(chat_id: int, from_user: int, to_user: int, value: int):
    cursor.execute(
        """
        INSERT INTO reputation (chat_id, from_user, to_user, value, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (chat_id, from_user, to_user, value, datetime.utcnow().isoformat())
    )
    conn.commit()


def get_rep(chat_id: int, user_id: int):
    cursor.execute(
        """
        SELECT
            SUM(CASE WHEN value = 1 THEN 1 ELSE 0 END),
            SUM(CASE WHEN value = -1 THEN 1 ELSE 0 END)
        FROM reputation
        WHERE chat_id = ? AND to_user = ?
        """,
        (chat_id, user_id)
    )
    plus, minus = cursor.fetchone()
    return plus or 0, minus or 0


def top_users_with_total(chat_id: int, hours: int, limit=5):
    since = datetime.utcnow() - timedelta(hours=hours)

    cursor.execute(
        """
        SELECT username, COUNT(*) as c
        FROM events
        WHERE chat_id = ?
          AND event_type = 'message'
          AND created_at >= ?
        GROUP BY user_id
        ORDER BY c DESC
        LIMIT ?
        """,
        (chat_id, since.isoformat(), limit)
    )
    top = cursor.fetchall()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM events
        WHERE chat_id = ?
          AND event_type = 'message'
          AND created_at >= ?
        """,
        (chat_id, since.isoformat())
    )
    total = cursor.fetchone()[0]

    return top, total

def get_user_achievements(chat_id: int, user_id: int):
    cursor.execute(
        """
        SELECT name, created_at
        FROM achievements
        WHERE chat_id = ? AND user_id = ?
        ORDER BY created_at
        """,
        (chat_id, user_id)
    )
    return cursor.fetchall()

def log_swear(chat_id: int, user_id: int, username: str):
    cursor.execute(
        """
        INSERT INTO swear_events (chat_id, user_id, username, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (chat_id, user_id, username, datetime.utcnow().isoformat())
    )
    conn.commit()

def get_top_swear_users(chat_id: int, days: int, limit: int = 5):
    since = datetime.utcnow() - timedelta(days=days)

    cursor.execute(
        """
        SELECT username, COUNT(*) as c
        FROM swear_events
        WHERE chat_id = ?
          AND created_at >= ?
        GROUP BY user_id
        ORDER BY c DESC
        LIMIT ?
        """,
        (chat_id, since.isoformat(), limit)
    )
    return cursor.fetchall()

def top_swearers_week(chat_id: int, limit=3):
    since = datetime.utcnow() - timedelta(days=7)

    cursor.execute(
        """
        SELECT username, COUNT(*) as c
        FROM swear_events
        WHERE chat_id = ?
          AND created_at >= ?
        GROUP BY user_id
        ORDER BY c DESC
        LIMIT ?
        """,
        (chat_id, since.isoformat(), limit)
    )
    return cursor.fetchall()

def get_top_swearers_last_week(chat_id: int, limit=3):
    today = datetime.utcnow().date()

    # понеділок цього тижня
    this_monday = today - timedelta(days=today.weekday())

    # минулий тиждень
    last_monday = this_monday - timedelta(days=7)
    last_sunday = this_monday

    cursor.execute(
        """
        SELECT username, COUNT(*) as c
        FROM swear_events
        WHERE chat_id = ?
          AND DATE(created_at) >= ?
          AND DATE(created_at) < ?
        GROUP BY user_id
        ORDER BY c DESC
        LIMIT ?
        """,
        (chat_id, last_monday.isoformat(), last_sunday.isoformat(), limit)
    )

    rows = cursor.fetchall()

    return rows, last_monday, last_sunday

def get_swear_stats(chat_id: int, days: int):
    since = datetime.utcnow() - timedelta(days=days)

    cursor.execute(
        """
        SELECT username, COUNT(*) as c
        FROM swear_events
        WHERE chat_id = ?
          AND created_at >= ?
        GROUP BY user_id
        ORDER BY c DESC
        """,
        (chat_id, since.isoformat())
    )
    users = cursor.fetchall()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM swear_events
        WHERE chat_id = ?
          AND created_at >= ?
        """,
        (chat_id, since.isoformat())
    )
    total = cursor.fetchone()[0]

    return users, total
