# routes/timer.py
import sqlite3
from flask import Blueprint, render_template

timer_bp = Blueprint("timer", __name__)

@timer_bp.route("/timer")
def timer():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, name FROM materials ORDER BY name ASC")
    materials = c.fetchall()
    conn.close()
    return render_template("timer.html", materials=materials)
