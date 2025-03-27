from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="cset155",
        database="exam_system"
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO accounts (username, email, password, account_type) VALUES (%s, %s, %s, %s)", (
            request.form["username"],
            request.form["email"],
            request.form["password"],
            request.form["account_type"]
        ))
        conn.commit()
        cur.close()
        conn.close()
        flash("Account Registered!")
        return redirect("/accounts")
    return render_template("register.html")


@app.route("/accounts")
def accounts():
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM accounts")
    accounts = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("accounts.html", accounts=accounts)


if __name__ == "__main__":
    app.run(debug=True)