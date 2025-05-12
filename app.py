import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from datetime import datetime, timedelta


import os
import csv
import io
import json

app = Flask(__name__)


os.makedirs("logs", exist_ok=True)


# ---------------------- 共通処理 ----------------------
def log_action(message):
    with open("logs/action.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {message}\n")


def get_events():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute(
        """
        SELECT title, description, event_datetime, remind_datetime, event_id, category, repeat, notified
        FROM events ORDER BY event_datetime ASC
    """
    )
    events = c.fetchall()
    conn.close()
    return events


# ---------------------- トップページ ----------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/calendar")
def calendar_view():
    events = get_events()
    return render_template("calendar.html", events=events)


@app.route("/filter", methods=["POST"])
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


@app.route("/register", methods=["GET", "POST"])
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
            return render_template(
                "register.html", error="過去の日時は登録できません。"
            )
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
        return redirect(url_for("calendar_view"))
    return render_template("register.html")


def insert_event(title, description, event_datetime, remind_datetime, category, repeat):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO events (user_id, title, description, event_datetime, remind_datetime, category, repeat)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (1, title, description, event_datetime, remind_datetime, category, repeat),
    )
    conn.commit()
    conn.close()


@app.route("/edit/<int:event_id>", methods=["GET", "POST"])
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
            return render_template(
                "edit.html",
                event_id=event_id,
                title=title,
                description=description,
                event_datetime=event_datetime,
                remind_offset=offset_min,
                category=category,
                repeat=repeat,
                error="過去の日時には変更できません。",
            )
        remind_dt = event_dt - timedelta(minutes=offset_min)
        c.execute(
            """
            UPDATE events SET title=?, description=?, event_datetime=?, remind_datetime=?, category=?, repeat=?, notified=0
            WHERE event_id=?
        """,
            (
                title,
                description,
                event_datetime,
                remind_dt.strftime("%Y-%m-%dT%H:%M"),
                category,
                repeat,
                event_id,
            ),
        )
        conn.commit()
        conn.close()
        log_action(f"✏️ 編集: {title}（ID={event_id}）")
        return redirect(url_for("calendar_view"))
    c.execute(
        "SELECT title, description, event_datetime, remind_datetime, category, repeat FROM events WHERE event_id=?",
        (event_id,),
    )
    event = c.fetchone()
    conn.close()
    if not event:
        return "Event not found", 404
    dt1 = datetime.strptime(event[2], "%Y-%m-%dT%H:%M")
    dt2 = datetime.strptime(event[3], "%Y-%m-%dT%H:%M")
    offset = int((dt1 - dt2).total_seconds() // 60)
    return render_template(
        "edit.html",
        event_id=event_id,
        title=event[0],
        description=event[1],
        event_datetime=event[2],
        remind_offset=offset,
        category=event[4],
        repeat=event[5],
    )


@app.route("/delete/<int:event_id>", methods=["POST"])
def delete_event(event_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM events WHERE event_id = ?", (event_id,))
    conn.commit()
    conn.close()
    log_action(f"🗑️ 削除: ID={event_id}")
    return redirect(url_for("calendar_view"))


@app.route("/export/events")
def export_events():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute(
        """
        SELECT title, description, event_datetime, remind_datetime, category, repeat, notified
        FROM events ORDER BY event_datetime ASC
    """
    )
    rows = c.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["タイトル", "説明", "実行日時", "通知時刻", "カテゴリ", "繰り返し", "通知済み"]
    )
    for row in rows:
        writer.writerow(row)
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="events.csv",
    )


@app.route("/export/logs")
def export_logs():
    log_path = "logs/notify.log"
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日時", "内容"])
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("["):
                    timestamp, message = line.split("]", 1)
                    writer.writerow([timestamp.strip("["), message.strip()])
    except FileNotFoundError:
        writer.writerow(["ログファイルが見つかりませんでした。"])
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="notify_log.csv",
    )


@app.route("/api/events")
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
    events = [
        {"title": title, "start": dt, "color": color_map.get(category, "#cccccc")}
        for title, dt, category in rows
    ]
    return jsonify(events)


# ToDo一覧画面
@app.route("/todo")
def todo():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, title, is_done FROM todos ORDER BY created_at DESC")
    todos = c.fetchall()
    conn.close()
    return render_template("todo.html", todos=todos)


# ToDo追加処理
@app.route("/todo/add", methods=["POST"])
def add_todo():
    title = request.form["title"]
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO todos (title) VALUES (?)", (title,))
    conn.commit()
    conn.close()
    return redirect(url_for("todo"))


# 完了・未完了の切り替え
@app.route("/todo/done/<int:todo_id>")
def mark_done(todo_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    # 状態を反転
    c.execute("UPDATE todos SET is_done = NOT is_done WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("todo"))


# ToDo削除
@app.route("/todo/delete/<int:todo_id>")
def delete_todo(todo_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("todo"))


# タイマー画面（教材選択つき）
@app.route("/timer")
def timer():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, name FROM materials ORDER BY name ASC")
    materials = c.fetchall()
    conn.close()
    return render_template("timer.html", materials=materials)


# 教材一覧表示
@app.route("/materials")
def materials():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM materials ORDER BY name ASC")
    materials = c.fetchall()
    conn.close()
    return render_template("materials.html", materials=materials)


# 教材追加処理
@app.route("/materials/add", methods=["POST"])
def add_material():
    name = request.form["name"]
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO materials (name) VALUES (?)", (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"⚠️ 教材 '{name}' は既に登録されています")
    finally:
        conn.close()
    return redirect(url_for("materials"))


# 学習セッションの記録（POST）
@app.route("/log_study", methods=["POST"])
def log_study():
    data = request.get_json()
    material_id = data.get("material_id")
    start_time = data.get("start_time")
    end_time = data.get("end_time")

    # 所要時間（秒）
    from datetime import datetime

    fmt = "%Y-%m-%dT%H:%M:%S"
    start_dt = datetime.strptime(start_time[:19], fmt)
    end_dt = datetime.strptime(end_time[:19], fmt)
    duration = int((end_dt - start_dt).total_seconds())

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO study_sessions (material_id, start_time, end_time, duration) VALUES (?, ?, ?, ?)",
        (material_id, start_time, end_time, duration),
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})


# 学習ログ画面
@app.route("/study_log")
def study_log():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # セッション一覧（教材名・開始・終了・所要時間）
    c.execute(
        """
        SELECT m.name, s.start_time, s.end_time, s.duration
        FROM study_sessions s
        JOIN materials m ON s.material_id = m.id
        ORDER BY s.start_time DESC
    """
    )
    sessions = c.fetchall()

    # 教材ごとの合計学習時間（秒→分（小数）に）
    c.execute(
        """
        SELECT m.name, SUM(s.duration)
        FROM study_sessions s
        JOIN materials m ON s.material_id = m.id
        GROUP BY m.name
        ORDER BY SUM(s.duration) DESC
    """
    )
    rows = c.fetchall()
    conn.close()

    labels = [row[0] for row in rows]
    data = [round(row[1] / 60, 2) for row in rows]  # ✅ 小数に変更

    return render_template(
        "study_log.html",
        sessions=sessions,
        chart_labels=json.dumps(labels, ensure_ascii=False),
        chart_data=json.dumps(data),
    )


@app.route("/materials/edit/<int:material_id>", methods=["GET", "POST"])
def edit_material(material_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST":
        new_name = request.form["name"]
        c.execute("UPDATE materials SET name = ? WHERE id = ?", (new_name, material_id))
        conn.commit()
        conn.close()
        return redirect(url_for("materials"))

    c.execute("SELECT id, name FROM materials WHERE id = ?", (material_id,))
    material = c.fetchone()
    conn.close()

    if not material:
        return "教材が見つかりません", 404

    return render_template("edit_material.html", material=material)


@app.route("/materials/delete/<int:material_id>", methods=["POST"])
def delete_material(material_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM materials WHERE id = ?", (material_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("materials"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
