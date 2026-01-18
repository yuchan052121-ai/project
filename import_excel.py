import pandas as pd
import sqlite3

DB = "reviews.db"
EXCEL = "社会工学類授業_df.xlsx"

df = pd.read_excel(EXCEL)

conn = sqlite3.connect(DB)
c = conn.cursor()

for _, r in df.iterrows():
    try:
        c.execute("""
        INSERT INTO courses (code, title, area, year, schedule)
        VALUES (?, ?, ?, ?, ?)
        """, (
            r["科目番号"],
            r["授業科目名"],
            r["専攻区分"],
            r["標準履修年次"],
            r["時間割"]
        ))
    except sqlite3.IntegrityError:
        pass

conn.commit()
conn.close()
print("Excel import finished.")
