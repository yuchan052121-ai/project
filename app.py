#!/usr/bin/env python
# coding: utf-8

# In[1]:


from flask import Flask, g, render_template, request, redirect, url_for, flash
import sqlite3
import hashlib
import datetime
from typing import Tuple

DATABASE = "reviews.db"
PER_PAGE = 50

app = Flask(__name__)
app.secret_key = "replace-with-a-secure-random-key"  # 本番ではランダムなシークレットに変更

# ---------- DB helpers ----------
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exc):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

# ---------- util ----------
def make_user_id(name: str) -> str:
    return hashlib.sha256(name.encode("utf-8")).hexdigest()[:16]

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# ---------- routes ----------
@app.route("/")
def index():
    courses = query_db("SELECT id, code, title FROM courses ORDER BY code")
    return render_template("index.html", courses=courses)

@app.route("/course/<int:course_id>/")
@app.route("/course/<int:course_id>/page/<int:page>/")
def course_view(course_id, page=1):
    db = get_db()
    # course
    course = query_db("SELECT * FROM courses WHERE id=?", (course_id,), one=True)
    if not course:
        return "Course not found", 404

    # filters from querystring
    min_rating = request.args.get("min_rating", type=int)
    q = "SELECT id, user_id, rating, comment, created_at FROM reviews WHERE course_id=? AND active=1"
    params = [course_id]
    if min_rating is not None:
        q += " AND rating>=?"
        params.append(min_rating)
    q += " ORDER BY created_at DESC"
    rows = query_db(q, tuple(params))

    # pagination
    total = len(rows)
    pages = (total + PER_PAGE - 1) // PER_PAGE
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    page_rows = rows[start:end]

    return render_template("course.html",
                           course=course,
                           reviews=page_rows,
                           page=page,
                           pages=pages,
                           total=total,
                           has_next=end < total,
                           has_prev=start > 0,
                           min_rating=min_rating)

@app.route("/course/<int:course_id>/add/", methods=["GET", "POST"])
def add_review(course_id):
    db = get_db()
    course = query_db("SELECT * FROM courses WHERE id=?", (course_id,), one=True)
    if not course:
        return "Course not found", 404

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        rating = request.form.get("rating", type=int)
        comment = request.form.get("comment", "").strip()
        if not name or not rating or rating < 1 or rating > 5:
            flash("名前と1〜5の評価を入力してください。")
            return redirect(url_for("add_review", course_id=course_id))

        user_id = make_user_id(name)
        now = datetime.datetime.utcnow().isoformat()

        try:
            db.execute(
                "INSERT INTO reviews (course_id, user_id, rating, comment, created_at, active) VALUES (?,?,?,?,?,1)",
                (course_id, user_id, rating, comment, now)
            )
            db.commit()
            flash("レビューを登録しました。")
        except sqlite3.IntegrityError:
            # 既にアクティブレビューがある → まず取消が必要
            flash("同じユーザの有効なレビューが既に存在します。まず取消してください。")

        return redirect(url_for("course_view", course_id=course_id))

    return render_template("add_review.html", course=course)

@app.route("/course/<int:course_id>/cancel", methods=["POST"])
def cancel_review(course_id):
    name = request.form.get("name", "").strip()
    if not name:
        flash("名前を入力してください。")
        return redirect(url_for("course_view", course_id=course_id))

    user_id = make_user_id(name)
    db = get_db()

    # find active review
    cur = db.execute("SELECT id FROM reviews WHERE course_id=? AND user_id=? AND active=1 ORDER BY created_at DESC LIMIT 1",
                     (course_id, user_id))
    row = cur.fetchone()
    cur.close()
    if not row:
        flash("アクティブなレビューが見つかりません。")
        return redirect(url_for("course_view", course_id=course_id))

    # delete any old active=0 to avoid UNIQUE violation, then set active=0
    db.execute("DELETE FROM reviews WHERE course_id=? AND user_id=? AND active=0", (course_id, user_id))
    db.execute("UPDATE reviews SET active=0 WHERE id=?", (row["id"],))
    db.commit()
    flash("レビューを取消しました。")
    return redirect(url_for("course_view", course_id=course_id))

# ---------- run ----------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)


# In[ ]:




