import pandas as pd
import sqlite3

df = pd.read_excel("data/社会工学類授業_df.xlsx")

conn = sqlite3.connect("reviews.db")
c = conn.cursor()

for _, row in df.iterrows():
    try:
        c.execute("""
        INSERT INTO courses (code, title, area, grade, timetable)
        VALUES (?, ?, ?, ?, ?)
        """, (
            row["科目番号"],
            row["授業科目名"],
            row["専攻区分"],
            row["標準履修年次"],
            row["時間割"]
        ))
    except:
        pass

conn.commit()
conn.close()
print("Excel imported")
