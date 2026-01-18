import sqlite3

DB_NAME = "reviews.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # ===== courses テーブル =====
    # Excel（社会工学類授業_df.xlsx）と連携
    c.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,          -- 科目番号
        title TEXT NOT NULL,       -- 授業科目名
        area TEXT NOT NULL,        -- 専攻区分
        grade TEXT NOT NULL,       -- 標準履修年次
        timetable TEXT NOT NULL    -- 時間割（学期＋曜時限）
    )
    """)

    # ===== reviews テーブル =====
    # 星評価4項目 + コメント + 重複投稿防止
    c.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        user_id TEXT NOT NULL,

        recommend INTEGER NOT NULL CHECK(recommend BETWEEN 1 AND 5),
        difficulty INTEGER NOT NULL CHECK(difficulty BETWEEN 1 AND 5),
        fun INTEGER NOT NULL CHECK(fun BETWEEN 1 AND 5),
        learning INTEGER NOT NULL CHECK(learning BETWEEN 1 AND 5),

        comment TEXT NOT NULL,
        created_at TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1,

        FOREIGN KEY (course_id) REFERENCES courses(id),
        UNIQUE(course_id, user_id, active)
    )
    """)

    conn.commit()
    conn.close()
    print("✅ データベース初期化が完了しました")

if __name__ == "__main__":
    init_db()
