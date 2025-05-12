# routes/todo.py
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for

todo_bp = Blueprint("todo", __name__)

@todo_bp.route("/todo")
def todo():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, title, is_done FROM todos ORDER BY created_at DESC")
    todos = c.fetchall()
    conn.close()
    return render_template("todo.html", todos=todos)


@todo_bp.route("/todo/add", methods=["POST"])
def add_todo():
    title = request.form["title"]
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO todos (title) VALUES (?)", (title,))
    conn.commit()
    conn.close()
    return redirect(url_for("todo.todo"))


@todo_bp.route("/todo/done/<int:todo_id>")
def mark_done(todo_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE todos SET is_done = NOT is_done WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("todo.todo"))


@todo_bp.route("/todo/delete/<int:todo_id>")
def delete_todo(todo_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("todo.todo"))
