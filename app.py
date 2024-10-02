import os
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL
from helpers import error, login_required

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///done.db")

@app.after_request
def add_headers(response):
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/todo", methods=["GET", "POST"])
@login_required
def manage_todo():
    username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]
    todo_items = db.execute("SELECT activity FROM ?", username)

    tasks = [activity['activity'] for activity in todo_items] if todo_items else []
    input_task = request.form.get("task")

    if request.method == "GET" or not input_task:
        return render_template("todo.html", tasks=tasks)

    if not db.execute("SELECT activity FROM ? WHERE activity=?", username, input_task):
        db.execute("INSERT INTO ? (activity) VALUES (?)", username, input_task)
        tasks.append(input_task)

    return redirect('/todo')

@app.route("/delete", methods=["GET", "POST"])
@login_required
def remove_task():
    if request.method == 'GET':
        return redirect('/todo')

    task = request.form.get("task")
    user = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]['username']

    if not task:
        return redirect('/todo')

    db.execute("DELETE FROM ? WHERE activity = ?", user, task)
    return redirect('/todo')

@app.route("/edit", methods=["GET", "POST"])
@login_required
def modify_task():
    if request.method == 'GET':
        return redirect('/todo')

    username = db.execute("SELECT username FROM users WHERE id = ?", session['user_id'])[0]['username']
    task = request.form.get("task")

    if not task:
        return redirect('/todo')

    session['recent_id'] = db.execute("SELECT id FROM ? WHERE activity = ?", username, task)[0]['id']
    return render_template("edit.html", task=task)

@app.route("/alter-edit", methods=["GET", "POST"])
@login_required
def update_task():
    if request.method == 'GET':
        return redirect('/todo')

    username = db.execute("SELECT username FROM users WHERE id = ?", session['user_id'])[0]['username']
    task = request.form.get("task")

    if not task:
        return redirect('/todo')

    db.execute("UPDATE ? SET activity = ? WHERE id = ?", username, task, session['recent_id'])
    session['recent_id'] = None
    return redirect('/todo')

@app.route("/login", methods=["GET", "POST"])
def login_user():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return error("must provide username", 400)
        elif not password:
            return error("must provide password", 400)

        user_data = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(user_data) != 1 or not check_password_hash(user_data[0]["hash"], password):
            return error("invalid username and/or password", 400)

        session["user_id"] = user_data[0]["id"]
        return redirect("/todo")
    return render_template("login.html")

@app.route("/logout")
def logout_user():
    session.clear()
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register_user():
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username").strip()
    password = request.form.get("password").strip()
    confirm_password = request.form.get("confirmation").strip()

    existing_user = db.execute("SELECT username FROM users WHERE username = ?", username)

    if not username.isalpha():
        return error("username must only contain Latin letters", 400)
    elif not username:
        return error("must provide username", 400)
    elif not password:
        return error("must provide password", 400)
    elif password != confirm_password:
        return error("passwords must match", 400)
    elif existing_user:
        return error("username already in use", 400)

    hashed_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)
    db.execute("INSERT INTO users(username, hash) VALUES (?,?)", username, hashed_password)
    db.execute("CREATE TABLE ? (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, activity TEXT NOT NULL)", username)

    user_id = db.execute("SELECT id FROM users WHERE username = ?", username)
    session["user_id"] = user_id[0]["id"]
    return redirect("/todo")

@app.route("/password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "GET":
        return render_template("password_change.html")

    username = db.execute("SELECT username, hash FROM users WHERE id = ?", session["user_id"])
    old_hash = username[0]["hash"]
    username = username[0]["username"]

    if not check_password_hash(old_hash, request.form.get("old_password")):
        return error("incorrect current password", 400)

    new_password = request.form.get("password")
    confirm_new_password = request.form.get("confirmation")

    if new_password != confirm_new_password:
        return error("passwords do not match", 400)

    new_hash = generate_password_hash(new_password, method="pbkdf2:sha256", salt_length=8)
    session.clear()
    db.execute("UPDATE users SET hash = ? WHERE username = ?", new_hash, username)

    user_id = db.execute("SELECT id FROM users WHERE username = ?", username)
    session["user_id"] = user_id[0]["id"]

    return redirect("/todo")
