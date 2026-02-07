from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, request, session, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DB_PATH = Path(__file__).resolve().parent / "expense_planner.db"

app = Flask(__name__, static_folder=str(FRONTEND_DIR / "static"), static_url_path="/static")
app.secret_key = os.environ.get("SECRET_KEY", "college-project-secret")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            bio TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            period TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            note TEXT DEFAULT '',
            image_url TEXT DEFAULT '',
            spent_on TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    conn.commit()
    conn.close()


def require_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "Please login first."}), 401
        return func(*args, **kwargs)

    return wrapper


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.post("/api/signup")
def signup():
    data = request.get_json(force=True)
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or len(password) < 6:
        return jsonify({"error": "Use a name, valid email, and password with 6+ chars."}), 400

    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Email already registered."}), 400

    user_id = cur.lastrowid
    session["user_id"] = user_id
    session["name"] = name
    conn.close()
    return jsonify({"message": "Account created.", "name": name})


@app.post("/api/login")
def login():
    data = request.get_json(force=True)
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "Invalid login details."}), 401

    session["user_id"] = row["id"]
    session["name"] = row["name"]
    return jsonify({"message": "Welcome back!", "name": row["name"]})


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out."})


@app.get("/api/me")
@require_login
def me():
    conn = get_db()
    user = conn.execute(
        "SELECT id, name, email, bio FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()
    conn.close()
    return jsonify(dict(user))


@app.post("/api/budgets")
@require_login
def add_budget():
    data = request.get_json(force=True)
    category = data.get("category", "").strip()
    period = data.get("period", "Monthly")
    amount = float(data.get("amount", 0))

    if not category or amount <= 0:
        return jsonify({"error": "Budget needs a category and positive amount."}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO budgets (user_id, category, amount, period, created_at) VALUES (?, ?, ?, ?, ?)",
        (session["user_id"], category, amount, period, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Budget added."})


@app.get("/api/budgets")
@require_login
def list_budgets():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, category, amount, period, created_at FROM budgets WHERE user_id = ? ORDER BY id DESC",
        (session["user_id"],),
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.post("/api/expenses")
@require_login
def add_expense():
    data = request.get_json(force=True)
    title = data.get("title", "").strip()
    category = data.get("category", "").strip() or "General"
    note = data.get("note", "").strip()
    image_url = data.get("image_url", "").strip()
    spent_on = data.get("spent_on", datetime.utcnow().date().isoformat())
    amount = float(data.get("amount", 0))

    if not title or amount <= 0:
        return jsonify({"error": "Expense needs a title and positive amount."}), 400

    conn = get_db()
    conn.execute(
        """
        INSERT INTO expenses (user_id, title, category, amount, note, image_url, spent_on, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session["user_id"],
            title,
            category,
            amount,
            note,
            image_url,
            spent_on,
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Expense saved."})


@app.get("/api/expenses")
@require_login
def list_expenses():
    conn = get_db()
    rows = conn.execute(
        """
        SELECT id, title, category, amount, note, image_url, spent_on, created_at
        FROM expenses WHERE user_id = ? ORDER BY spent_on DESC, id DESC
        """,
        (session["user_id"],),
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.post("/api/notes")
@require_login
def add_note():
    data = request.get_json(force=True)
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()

    if not title or not content:
        return jsonify({"error": "Note needs title and content."}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO notes (user_id, title, content, created_at) VALUES (?, ?, ?, ?)",
        (session["user_id"], title, content, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Note added."})


@app.get("/api/notes")
@require_login
def list_notes():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, title, content, created_at FROM notes WHERE user_id = ? ORDER BY id DESC",
        (session["user_id"],),
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.post("/api/messages")
@require_login
def send_message():
    data = request.get_json(force=True)
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Message is empty."}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO messages (user_id, username, text, created_at) VALUES (?, ?, ?, ?)",
        (session["user_id"], session.get("name", "User"), text, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Message sent."})


@app.get("/api/messages")
@require_login
def list_messages():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, username, text, created_at FROM messages ORDER BY id DESC LIMIT 40"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows][::-1])


@app.get("/api/summary")
@require_login
def summary():
    conn = get_db()
    budget_total = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM budgets WHERE user_id = ?", (session["user_id"],)
    ).fetchone()["total"]
    expense_total = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = ?", (session["user_id"],)
    ).fetchone()["total"]
    tx_count = conn.execute(
        "SELECT COUNT(*) AS count FROM expenses WHERE user_id = ?", (session["user_id"],)
    ).fetchone()["count"]
    conn.close()

    return jsonify(
        {
            "budget_total": round(budget_total, 2),
            "expense_total": round(expense_total, 2),
            "remaining": round(budget_total - expense_total, 2),
            "transaction_count": tx_count,
            "username": session.get("name", "Student"),
        }
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
