# init_db.py
import sqlite3

DB = "reviews.db"

def init_db(path=DB):
    conn = sqlite3.connect(path)
    c = conn.cursor()

    # courses テーブル（Excel対応）
    c.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,          -- 科目番号
        title TEXT,                -- 授業科目名
        area TEXT,                 -- 専攻区分
        year TEXT,                 -- 標準履修年次
        schedule TEXT              -- 時間割
    )
    """)

    # reviews テーブル（評価4項目）
    c.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        user_id TEXT,
        recommend INTEGER CHECK(recommend BETWEEN 1 AND 5),
        difficulty INTEGER CHECK(difficulty BETWEEN 1 AND 5),
        fun INTEGER CHECK(fun BETWEEN 1 AND 5),
        learning INTEGER CHECK(learning BETWEEN 1 AND 5),
        attendance_required INTEGER DEFAULT 0,
        assessment TEXT,
        comment TEXT,
        created_at TIMESTAMP,
        active INTEGER DEFAULT 1,
        UNIQUE(course_id, user_id, active)
    )
    """)

    conn.commit()
    return conn

if __name__ == "__main__":
    init_db()
    print("DB initialized.")
