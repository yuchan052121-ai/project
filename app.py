#!/usr/bin/env python
# coding: utf-8

from flask import Flask, g, render_template, request, redirect, url_for, flash
import sqlite3
import hashlib
import datetime

DATABASE = "reviews.db"
PER_PAGE = 50

app = Flask(__name__)
app.secret_key = "replace-with-a-secure-random-key"

# =====================
# DB helpers
# =====================
def get_db():
    if "_database" not in g:
        g._database = sqlite3.connect(DATABASE)
        g._database.row_factory = sqlite3.Row
    return g._database

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop("_database", None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows

# =====================
# util
# =====================
def make_user_id(name: str) -> str:
    return hashlib.sha256(name.encode("utf-8")).hexdigest()[:16]

# =====================
# routes
# =====================

# -------- TOP --------
@app.route("/")
def index():
    courses = query_db("""
        SELECT id, code, title, area, grade
        FROM courses
        ORDER BY code
    """)
    return render_template("index.html", courses=courses)

# -------- COURSE DETAIL --------
@app.route("/course/<int:course_id>/")
@app.route("/course/<int:course_id>/page/<int:page>/")
def course_view(course_id, page=1):
    # course info
    course = query_db("SELECT * FROM courses WHERE id=?", (course_id,), one=True)
    if not course:
        return "Course not found", 404

    # ---- filters ----
    min_recommend = request.args.get("min_recommend", type=int)

    sql = """
        SELECT
            id, user_id,
            recommend, difficulty, fun, learning,
            comment, created_at
        FROM reviews
        WHERE course_id=? AND active=1
    """
    params = [course_id]

    if min_recommend:
        sql += " AND recommend >= ?"
        params.append(min_recommend)

    sql += " ORDER BY created_at DESC"

    reviews_all = query_db(sql, tuple(params))

    # ---- pagination ----
    total = len(reviews_all)
    pages = (total + PER_PAGE - 1) // PER_PAGE
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    reviews = reviews_all[start:end]

    # ---- average rating ----
    avg = query_db("""
        SELECT
            ROUND(AVG(recommend), 2) AS recommend,
            ROUND(AVG(difficulty), 2) AS difficulty,
            ROUND(AVG(fun), 2) AS fun,
            ROUND(AVG(learning), 2) AS learning
        FROM reviews
        WHERE course_id=? AND active=1
    """, (course_id,), one=True)

    return render_template(
        "course.html",
        course=course,
        reviews=reviews,
        avg=avg,
        page=page,
        pages=pages,
        total=total,
        has_next=end < total,
        has_prev=start > 0,
        min_recommend=min_recommend
    )

# -------- ADD REVIEW --------
@app.route("/course/<int:course_id>/add/", methods=["GET", "POST"])
def add_review(course_id):
    course = query_db("SELECT * FROM courses WHERE id=?", (course_id,), one=True)
    if not course:
        return "Course not found", 404

    if request.method == "POST":
        name = request.form["name"]
        user_id = make_user_id(name)

        data = (
            course_id,
            user_id,
            int(request.form["recommend"]),
            int(request.form["difficulty"]),
            int(request.form["fun"]),
            int(request.form["learning"]),
            request.form["comment"],
            datetime.datetime.now().isoformat()
        )

        db = get_db()
        try:
            db.execute("""
                INSERT INTO reviews
                (course_id, user_id,
                 recommend, difficulty, fun, learning,
                 comment, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            db.commit()
            flash("レビューを投稿しました")
        except sqlite3.IntegrityError:
            flash("すでにこの授業にレビューを投稿しています（取消後に再投稿できます）")

        return redirect(url_for("course_view", course_id=course_id))

    return render_template("add_review.html", course=course)

# -------- CANCEL REVIEW --------
@app.route("/course/<int:course_id>/cancel/", methods=["POST"])
def cancel_review(course_id):
    name = request.form["name"]
    user_id = make_user_id(name)

    db = get_db()
    cur = db.execute("""
        SELECT id FROM reviews
        WHERE course_id=? AND user_id=? AND active=1
    """, (course_id, user_id))
    row = cur.fetchone()

    if not row:
        flash("アクティブなレビューが見つかりません")
    else:
        db.execute("UPDATE reviews SET active=0 WHERE id=?", (row["id"],))
        db.commit()
        flash("レビューを取消しました")

    return redirect(url_for("course_view", course_id=course_id))

# -------- SEARCH --------
@app.route("/search/")
def search():
    code = request.args.get("code", "")
    title = request.args.get("title", "")
    area = request.args.get("area", "")
    grade = request.args.get("grade", "")

    sql = "SELECT * FROM courses WHERE 1=1"
    params = []

    if code:
        sql += " AND code LIKE ?"
        params.append(f"%{code}%")
    if title:
        sql += " AND title LIKE ?"
        params.append(f"%{title}%")
    if area:
        sql += " AND area=?"
        params.append(area)
    if grade:
        sql += " AND grade=?"
        params.append(grade)

    courses = query_db(sql, tuple(params))
    return render_template("search.html", courses=courses)

# =====================
# run
# =====================
if __name__ == "__main__":
    app.run(debug=True)





