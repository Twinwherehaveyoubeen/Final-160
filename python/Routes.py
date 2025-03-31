from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
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
    if 'account_type' not in session or session['account_type'] != 'teacher':
        flash("Only teachers can edit tests.")
        return redirect("/")

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

@app.route("/delete/<int:test_id>", methods=["POST"])
def delete_test(test_id):
    if 'account_type' not in session or session['account_type'] != 'teacher':
        flash("Only teachers can delete tests.")
        return redirect("/")

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tests WHERE id = %s", (test_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Test deleted.")
    return redirect("/tests")

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

@app.route("/tests")
def tests():
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM tests")
    tests = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("tests.html", tests=tests)

@app.route("/grade_test", methods=["GET", "POST"])
def grade_test():
    conn = connect_db()
    cur = conn.cursor(dictionary=True)

    if request.method == 'POST':
        student_id = request.form['student_id']
        test_id = request.form['test_id']
        marks = request.form['marks']
        cur.execute("REPLACE INTO marks (student_id, test_id, marks) VALUES (%s, %s, %s)", (student_id, test_id, marks))
        conn.commit()
        flash("Marks submitted successfully")

    cur.execute("SELECT ta.student_id, ta.test_id, a.username AS student_name, t.test_name FROM test_attempts ta JOIN accounts a ON ta.student_id = a.id JOIN tests t ON ta.test_id = t.id")
    attempts = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('grade_test.html', attempts=attempts)

@app.route("/tests_info")
def tests_info():
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT t.id, t.test_name, a.username AS teacher, COUNT(ta.student_id) AS taken_by FROM tests t JOIN accounts a ON t.teacher_id = a.id LEFT JOIN test_attempts ta ON t.id = ta.test_id GROUP BY t.id")
    tests = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("tests_info.html", tests=tests)

@app.route("/test_details/<int:test_id>")
def test_details(test_id):
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT a.username AS student, m.marks, t.test_name, t.id, gr.username AS graded_by
        FROM test_attempts ta
        JOIN accounts a ON ta.student_id = a.id
        JOIN tests t ON ta.test_id = t.id
        LEFT JOIN marks m ON m.student_id = a.id AND m.test_id = t.id
        LEFT JOIN accounts gr ON gr.id = t.teacher_id
        WHERE ta.test_id = %s
    """, (test_id,))
    details = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("test_details.html", details=details)

@app.route("/student_results")
def student_results():
    student_id = request.args.get('student_id')
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    if student_id:
        cur.execute("SELECT t.test_name, m.marks FROM marks m JOIN tests t ON m.test_id = t.id WHERE m.student_id = %s", (student_id,))
        results = cur.fetchall()
    else:
        results = []
    cur.execute("SELECT id, username FROM accounts WHERE account_type='student'")
    students = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("student_results.html", students=students, results=results)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = connect_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM accounts WHERE email = %s AND password = %s", (email, password))
        account = cur.fetchone()
        cur.close()
        conn.close()

        if account:
            session['user_id'] = account['id']
            session['account_type'] = account['account_type']
            session['username'] = account['username']
            flash("Logged in successfully!")
            return redirect("/")
        else:
            flash("Invalid login. Try again.")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
