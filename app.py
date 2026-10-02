from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "student_management_secret_key"

DATABASE = "database.db"


# =========================
# DATABASE CONNECTION
# =========================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# CREATE DATABASE TABLES
# =========================

def init_db():

    conn = get_db()

    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Students table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            department TEXT,
            year TEXT,
            marks TEXT,
            attendance TEXT
        )
    """)

    conn.commit()
    conn.close()


# =========================
# HOME / LOGIN
# =========================

@app.route("/")
def login():
    return render_template("login.html")


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db()

        try:
            conn.execute("""
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
            """, (name, email, password))

            conn.commit()
            conn.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            conn.close()
            return "Email already registered"

    return render_template("register.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login_user():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db()

        user = conn.execute("""
            SELECT * FROM users
            WHERE email = ? AND password = ?
        """, (email, password)).fetchone()

        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("dashboard"))

        return "Invalid email or password"

    return render_template("login.html")


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    conn = get_db()

    total_students = conn.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_students=total_students
    )


# =========================
# STUDENTS LIST
# =========================

@app.route("/students")
def students():

    search = request.args.get("search", "")
    department = request.args.get("department", "")
    year = request.args.get("year", "")

    conn = get_db()

    query = "SELECT * FROM students WHERE 1=1"
    params = []

    if search:

        query += """
            AND (
                name LIKE ?
                OR email LIKE ?
                OR CAST(id AS TEXT) LIKE ?
            )
        """

        search_value = "%" + search + "%"

        params.extend([
            search_value,
            search_value,
            search_value
        ])

    if department:

        query += " AND department = ?"
        params.append(department)

    if year:

        query += " AND year = ?"
        params.append(year)

    query += " ORDER BY id DESC"

    students = conn.execute(
        query,
        params
    ).fetchall()

    conn.close()

    return render_template(
        "students.html",
        students=students,
        search=search,
        department=department,
        year=year
    )


# =========================
# ADD STUDENT
# =========================

@app.route("/add-student", methods=["GET", "POST"])
def add_student():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        department = request.form.get("department")
        year = request.form.get("year")
        marks = request.form.get("marks")
        attendance = request.form.get("attendance")

        conn = get_db()

        conn.execute("""
            INSERT INTO students
            (
                name,
                email,
                phone,
                department,
                year,
                marks,
                attendance
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            email,
            phone,
            department,
            year,
            marks,
            attendance
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("students"))

    return render_template("add_student.html")


# =========================
# STUDENT DETAILS
# =========================

@app.route("/student-details/<int:id>")
def student_details(id):

    conn = get_db()

    student = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (id,)
    ).fetchone()

    conn.close()

    if student is None:
        return "Student not found", 404

    return render_template(
        "student_details.html",
        student=student
    )


# =========================
# EDIT STUDENT
# =========================

@app.route("/edit-student/<int:id>", methods=["GET", "POST"])
def edit_student(id):

    conn = get_db()

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        department = request.form.get("department")
        year = request.form.get("year")
        marks = request.form.get("marks")
        attendance = request.form.get("attendance")

        conn.execute("""
            UPDATE students
            SET
                name = ?,
                email = ?,
                phone = ?,
                department = ?,
                year = ?,
                marks = ?,
                attendance = ?
            WHERE id = ?
        """, (
            name,
            email,
            phone,
            department,
            year,
            marks,
            attendance,
            id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("students"))

    student = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (id,)
    ).fetchone()

    conn.close()

    if student is None:
        return "Student not found", 404

    return render_template(
        "edit_student.html",
        student=student
    )


# =========================
# DELETE STUDENT
# =========================

@app.route("/delete-student/<int:id>")
def delete_student(id):

    conn = get_db()

    conn.execute(
        "DELETE FROM students WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("students"))


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":

    init_db()

    app.run(debug=True)