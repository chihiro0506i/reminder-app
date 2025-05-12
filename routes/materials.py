# routes/materials.py
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for

materials_bp = Blueprint("materials", __name__)

@materials_bp.route("/materials")
def materials():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM materials ORDER BY name ASC")
    materials = c.fetchall()
    conn.close()
    return render_template("materials.html", materials=materials)


@materials_bp.route("/materials/add", methods=["POST"])
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
    return redirect(url_for("materials.materials"))


@materials_bp.route("/materials/edit/<int:material_id>", methods=["GET", "POST"])
def edit_material(material_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST":
        new_name = request.form["name"]
        c.execute("UPDATE materials SET name = ? WHERE id = ?", (new_name, material_id))
        conn.commit()
        conn.close()
        return redirect(url_for("materials.materials"))

    c.execute("SELECT id, name FROM materials WHERE id = ?", (material_id,))
    material = c.fetchone()
    conn.close()

    if not material:
        return "教材が見つかりません", 404

    return render_template("edit_material.html", material=material)


@materials_bp.route("/materials/delete/<int:material_id>", methods=["POST"])
def delete_material(material_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM materials WHERE id = ?", (material_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("materials.materials"))
