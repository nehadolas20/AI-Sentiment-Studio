from flask import Flask, render_template, request, redirect, url_for, session
from textblob import TextBlob
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"
DB = "app.db"

def get_db():
    return sqlite3.connect(DB)

def init_db():
    con = get_db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        text TEXT,
        sentiment TEXT,
        time TEXT
    )
    """)

    con.commit()
    con.close()

init_db()

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        con = get_db()
        cur = con.cursor()
        cur.execute("SELECT id FROM users WHERE username=? AND password=?", (u, p))
        user = cur.fetchone()
        con.close()

        if user:
            session["user_id"] = user[0]
            session["username"] = u
            return redirect(url_for("dashboard"))
        else:
            msg = "Invalid credentials"

    return render_template("login.html", msg=msg)

@app.route("/register", methods=["GET", "POST"])
def register():
    msg = ""
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        try:
            con = get_db()
            cur = con.cursor()
            cur.execute("INSERT INTO users(username,password) VALUES(?,?)", (u, p))
            con.commit()
            con.close()
            return redirect(url_for("login"))
        except:
            msg = "Username already exists"

    return render_template("register.html", msg=msg)

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    result = ""
    if request.method == "POST":
        text = request.form["text"]
        blob = TextBlob(text)
        p = blob.sentiment.polarity

        if p > 0: label = "POSITIVE"
        elif p < 0: label = "NEGATIVE"
        else: label = "NEUTRAL"

        result = f"{label} ({round(p,2)})"

        con = get_db()
        cur = con.cursor()
        cur.execute("INSERT INTO history(user_id,text,sentiment,time) VALUES(?,?,?,?)",
                    (session["user_id"], text, result, datetime.now().strftime("%d-%m-%Y %H:%M")))
        con.commit()
        con.close()

    return render_template("dashboard.html", result=result, username=session["username"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
