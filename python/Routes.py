from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
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

@app.route('/styles/<path:filename>')
def styles(filename):
    return send_from_directory('styles', filename)

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

@app.route("/take_test/<int:test_id>", methods=["GET", "POST"])
def take_test(test_id):
    conn = connect_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM tests WHERE id = %s", (test_id,))
    test = cur.fetchone()
    cur.execute("SELECT * FROM questions WHERE test_id = %s", (test_id,))
    questions = cur.fetchall()
    cur.execute("SELECT * FROM accounts WHERE account_type='student'")
    students = cur.fetchall()

    if request.method == "POST":
        student_id = request.form["student_id"]
        cur.execute("SELECT * FROM test_attempts WHERE test_id = %s AND student_id = %s", (test_id, student_id))
        if cur.fetchone():
            return "You already took this test."

        cur.execute("INSERT INTO test_attempts (test_id, student_id, started_at, status) VALUES (%s, %s, NOW(), 'submitted')",
                    (test_id, student_id))

        for q in questions:
            answer = request.form.get("question_" + str(q["id"]), "")
            cur.execute("INSERT INTO responses (test_id, student_id, question_id, answer_text, submitted_at) VALUES (%s, %s, %s, %s, NOW())",
                        (test_id, student_id, q["id"], answer))

        conn.commit()
        cur.close()
        conn.close()
        return "Test submitted successfully!"

    cur.close()
    conn.close()
    return render_template("take_test.html", test=test, questions=questions, students=students)

@app.route("/edit/<int:test_id>", methods=["GET", "POST"])
def edit_test(test_id):
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    if request.method == "POST":
        new_name = request.form["test_name"]
        cur.execute("UPDATE tests SET test_name = %s WHERE id = %s", (new_name, test_id))
        conn.commit()
        cur.close()
        conn.close()
        return "Test name updated!"
    else:
        cur.execute("SELECT * FROM tests WHERE id = %s", (test_id,))
        test = cur.fetchone()
        cur.close()
        conn.close()
        return render_template("edit_test.html", test=test)

@app.route("/create_test", methods=["GET", "POST"])
def create_test():
    conn = connect_db()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        test_name = request.form["test_name"]
        teacher_id = request.form["teacher_id"]
        cur.execute("INSERT INTO tests (test_name, teacher_id, created_at) VALUES (%s, %s, NOW())", (test_name, teacher_id))
        test_id = cur.lastrowid

        questions_text = request.form["questions"]
        for q in questions_text.strip().split("\n"):
            if q.strip():
                cur.execute("INSERT INTO questions (test_id, question_text) VALUES (%s, %s)", (test_id, q.strip()))

        conn.commit()
        cur.close()
        conn.close()
        return "Test created successfully!"

    cur.execute("SELECT * FROM accounts WHERE account_type = 'teacher'")
    teachers = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("create_test.html", teachers=teachers)

if __name__ == "__main__":
    app.run(debug=True)
