from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import hashlib
import datetime

app = Flask(__name__)
app.secret_key = "project3-secret-key"

DB_NAME = "reviews.db"

# =========================
# DB 接続
# =========================
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# トップページ：授業一覧
# =========================
@app.route("/")
def index():
    db = get_db()
    courses = db.execute("""
        SELECT * FROM courses
        ORDER BY code
    """).fetchall()
    db.close()
    return render_template("index.html", courses=courses)


# =========================
# 授業詳細ページ
# =========================
@app.route("/course/<int:course_id>")
def course_view(course_id):
    db = get_db()

    course = db.execute(
        "SELECT * FROM courses WHERE id = ?",
        (course_id,)
    ).fetchone()

    reviews = db.execute("""
        SELECT * FROM reviews
        WHERE course_id = ? AND active = 1
        ORDER BY created_at DESC
    """, (course_id,)).fetchall()

    avg = db.execute("""
        SELECT
          ROUND(AVG(recommend), 2) AS recommend,
          ROUND(AVG(difficulty), 2) AS difficulty,
          ROUND(AVG(fun), 2) AS fun,
          ROUND(AVG(learning), 2) AS learning
        FROM reviews
        WHERE course_id = ? AND active = 1
    """, (course_id,)).fetchone()

    db.close()

    return render_template(
        "course.html",
        course=course,
        reviews=reviews,
        avg=avg
    )


# =========================
# レビュー投稿
# =========================
@app.route("/course/<int:course_id>/add", methods=["GET", "POST"])
def add_review(course_id):
    db = get_db()

    course = db.execute(
        "SELECT * FROM courses WHERE id = ?",
        (course_id,)
    ).fetchone()

    if request.method == "POST":
        name = request.form["name"]
        user_id = hashlib.sha256(name.encode()).hexdigest()

        recommend = int(request.form["recommend"])
        difficulty = int(request.form["difficulty"])
        fun = int(request.form["fun"])
        learning = int(request.form["learning"])

        attendance = 1 if "attendance" in request.form else 0
        assessment = request.form["assessment"]
        comment = request.form["comment"]

        try:
            db.execute("""
                INSERT INTO reviews
                (course_id, user_id, recommend, difficulty, fun, learning,
                 attendance, assessment, comment, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                course_id,
                user_id,
                recommend,
                difficulty,
                fun,
                learning,
                attendance,
                assessment,
                comment,
                datetime.datetime.now().isoformat()
            ))
            db.commit()
            flash("レビューを投稿しました")
        except sqlite3.IntegrityError:
            flash("この授業はすでにレビュー済みです（取消後に再投稿できます）")

        db.close()
        return redirect(url_for("course_view", course_id=course_id))

    db.close()
    return render_template("add_review.html", course=course)


# =========================
# レビュー取消
# =========================
@app.route("/review/<int:review_id>/cancel")
def cancel_review(review_id):
    db = get_db()
    db.execute(
        "UPDATE reviews SET active = 0 WHERE id = ?",
        (review_id,)
    )
    db.commit()
    db.close()
    flash("レビューを取り消しました")
    return redirect(request.referrer or url_for("index"))


# =========================
# 授業検索
# =========================
@app.route("/search")
def search():
    code = request.args.get("code", "")
    title = request.args.get("title", "")
    area = request.args.get("area", "")
    grade = request.args.get("grade", "")

    query = "SELECT * FROM courses WHERE 1=1"
    params = []

    if code:
        query += " AND code LIKE ?"
        params.append(f"%{code}%")

    if title:
        query += " AND title LIKE ?"
        params.append(f"%{title}%")

    if area:
        query += " AND area = ?"
        params.append(area)

    if grade:
        query += " AND grade = ?"
        params.append(grade)

    db = get_db()
    courses = db.execute(query, params).fetchall()
    db.close()

    return render_template("search.html", courses=courses)


# =========================
# 起動
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
