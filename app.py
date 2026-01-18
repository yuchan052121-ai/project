from flask import Flask, g, render_template, request, redirect, url_for, flash
import sqlite3
import hashlib
import datetime

DATABASE = "reviews.db"
PER_PAGE = 50

app = Flask(__name__)
app.secret_key = "replace-this"

def get_db():
    if not hasattr(g, "db"):
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = getattr(g, "db", None)
    if db:
        db.close()

def make_user_id(name):
    return hashlib.sha256(name.encode()).hexdigest()[:16]

def query_db(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rv = cur.fetchall()
    cur.close()
    return rv[0] if one and rv else rv

@app.route("/")
def index():
    courses = query_db("SELECT * FROM courses ORDER BY code")
    return render_template("index.html", courses=courses)

@app.route("/search/")
def search():
    sql = "SELECT * FROM courses WHERE 1=1"
    params = []

    for field in ["code", "title", "area", "year", "schedule"]:
        v = request.args.get(field, "").strip()
        if v:
            sql += f" AND {field} LIKE ?"
            params.append(f"%{v}%")

    courses = query_db(sql, params)
    return render_template("search_results.html", courses=courses, **request.args)

@app.route("/course/<int:course_id>/")
def course_view(course_id):
    course = query_db("SELECT * FROM courses WHERE id=?", (course_id,), one=True)
    reviews = query_db("""
        SELECT * FROM reviews
        WHERE course_id=? AND active=1
        ORDER BY created_at DESC
    """, (course_id,))
    return render_template("course.html", course=course, reviews=reviews, total=len(reviews))

@app.route("/course/<int:course_id>/add/", methods=["GET", "POST"])
def add_review(course_id):
    course = query_db("SELECT * FROM courses WHERE id=?", (course_id,), one=True)

    if request.method == "POST":
        name = request.form["name"]
        user_id = make_user_id(name)

        db = get_db()
        db.execute("""
            INSERT INTO reviews
            (course_id, user_id, recommend, difficulty, fun, learning,
             attendance_required, assessment, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            course_id, user_id,
            request.form["recommend"],
            request.form["difficulty"],
            request.form["fun"],
            request.form["learning"],
            1 if request.form.get("attendance") else 0,
            request.form["assessment"],
            request.form["comment"],
            datetime.datetime.utcnow().isoformat()
        ))
        db.commit()
        flash("レビューを投稿しました")
        return redirect(url_for("course_view", course_id=course_id))

    return render_template("add_review.html", course=course)
