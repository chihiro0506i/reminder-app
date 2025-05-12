# routes/study_log.py
import sqlite3
from flask import Blueprint, request, render_template, jsonify
import json
from datetime import datetime

study_log_bp = Blueprint("study_log", __name__)

@study_log_bp.route("/log_study", methods=["POST"])
def log_study():
    data = request.get_json()
    material_id = data.get("material_id")
    start_time = data.get("start_time")
    end_time = data.get("end_time")

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


@study_log_bp.route("/study_log")
def study_log():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        """
        SELECT m.name, s.start_time, s.end_time, s.duration
        FROM study_sessions s
        JOIN materials m ON s.material_id = m.id
        ORDER BY s.start_time DESC
    """
    )
    sessions = c.fetchall()

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
    data = [round(row[1] / 60, 2) for row in rows]

    return render_template(
        "study_log.html",
        sessions=sessions,
        chart_labels=json.dumps(labels, ensure_ascii=False),
        chart_data=json.dumps(data),
    )
