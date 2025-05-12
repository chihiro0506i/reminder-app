import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, send_file
from datetime import datetime, timedelta
import os
import csv
import io
import json

reminder_bp = Blueprint("reminder", __name__)

os.makedirs("logs", exist_ok=True)

# ---------------------- 共通処理 ----------------------
def log_action(message):
    with open("logs/action.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {message}\n")


def get_events():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        SELECT title, description, event_datetime, remind_datetime, event_id, category, repeat, notified
        FROM events ORDER BY event_datetime ASC
    """)
    events = c.fetchall()
    conn.close()
    return events

# ---------------------- トップページ ----------------------
@reminder_bp.route("/")
def index():
    return render_template("index.html")

@reminder_bp.route("/calendar")
def calendar_view():
    events = get_events()
    return render_template("calendar.html", events=events)

@reminder_bp.route("/filter", methods=["POST"])
def filter():
    category = request.form.get("category")
    notified = request.form.get("notified")
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    query = """
        SELECT title, description, event_datetime, remind_datetime, event_id, category, repeat, notified
        FROM events WHERE 1=1
    """
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if notified in ["0", "1"]:
        query += " AND notified = ?"
        params.append(int(notified))
    query += " ORDER BY event_datetime ASC"
    c.execute(query, params)
    events = c.fetchall()
    conn.close()
    return render_template("calendar.html", events=events)

@reminder_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        event_datetime = request.form["event_datetime"]
        offset_min = int(request.form["remind_offset"])
        category = request.form["category"]
        repeat = request.form["repeat"]
        event_dt = datetime.strptime(event_datetime, "%Y-%m-%dT%H:%M")
        if event_dt < datetime.now():
            return render_template("register.html", error="過去の日時は登録できません。")
        remind_dt = event_dt - timedelta(minutes=offset_min)
        insert_event(
            title,
            description,
            event_datetime,
            remind_dt.strftime("%Y-%m-%dT%H:%M"),
            category,
            repeat,
        )
        log_action(f"✅ 登録: {title}（{event_datetime}）")
        return redirect(url_for("reminder.calendar_view"))
    return render_template("register.html")

def insert_event(title, description, event_datetime, remind_datetime, category, repeat):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO events (user_id, title, description, event_datetime, remind_datetime, category, repeat)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (1, title, description, event_datetime, remind_datetime, category, repeat))
    conn.commit()
    conn.close()

@reminder_bp.route("/edit/<int:event_id>", methods=["GET", "POST"])
def edit_event(event_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        event_datetime = request.form["event_datetime"]
        offset_min = int(request.form["remind_offset"])
        category = request.form["category"]
        repeat = request.form["repeat"]
        event_dt = datetime.strptime(event_datetime, "%Y-%m-%dT%H:%M")
        if event_dt < datetime.now():
            return render_template("edit.html", event_id=event_id, title=title, description=description,
                                   event_datetime=event_datetime, remind_offset=offset_min,
                                   category=category, repeat=repeat,
                                   error="過去の日時には変更できません。")
        remind_dt = event_dt - timedelta(minutes=offset_min)
        c.execute("""
            UPDATE events SET title=?, description=?, event_datetime=?, remind_datetime=?, category=?, repeat=?, notified=0
            WHERE event_id=?
        """, (title, description, event_datetime, remind_dt.strftime("%Y-%m-%dT%H:%M"),
              category, repeat, event_id))
        conn.commit()
        conn.close()
        log_action(f"✏️ 編集: {title}（ID={event_id}）")
        return redirect(url_for("reminder.calendar_view"))
    c.execute("SELECT title, description, event_datetime, remind_datetime, category, repeat FROM events WHERE event_id=?", (event_id,))
    event = c.fetchone()
    conn.close()
    if not event:
        return "Event not found", 404
    dt1 = datetime.strptime(event[2], "%Y-%m-%dT%H:%M")
    dt2 = datetime.strptime(event[3], "%Y-%m-%dT%H:%M")
    offset = int((dt1 - dt2).total_seconds() // 60)
    return render_template("edit.html", event_id=event_id, title=event[0], description=event[1],
                           event_datetime=event[2], remind_offset=offset,
                           category=event[4], repeat=event[5])

@reminder_bp.route("/delete/<int:event_id>", methods=["POST"])
def delete_event(event_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM events WHERE event_id = ?", (event_id,))
    conn.commit()
    conn.close()
    log_action(f"🗑️ 削除: ID={event_id}")
    return redirect(url_for("reminder.calendar_view"))

@reminder_bp.route("/export/events")
def export_events():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        SELECT title, description, event_datetime, remind_datetime, category, repeat, notified
        FROM events ORDER BY event_datetime ASC
    """)
    rows = c.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["タイトル", "説明", "実行日時", "通知時刻", "カテゴリ", "繰り返し", "通知済み"])
    for row in rows:
        writer.writerow(row)
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode("utf-8-sig")),
                     mimetype="text/csv", as_attachment=True,
                     download_name="events.csv")

@reminder_bp.route("/api/events")
def api_events():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT title, event_datetime, category FROM events")
    rows = c.fetchall()
    conn.close()
    color_map = {
        "仕事": "#ff9999",
        "個人": "#99ff99",
        "勉強": "#9999ff",
        "健康": "#ffff99",
        "未分類": "#dddddd",
    }
    events = [{"title": title, "start": dt, "color": color_map.get(category, "#cccccc")} for title, dt, category in rows]
    return jsonify(events)
