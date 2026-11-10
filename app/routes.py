import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models import Student

bp = Blueprint("main", __name__)
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _registration_values(form_data):
    """Normalize registration fields and return an error for invalid input."""
    values = {
        "student_id": form_data.get("student_id", "").strip(),
        "full_name": form_data.get("full_name", "").strip(),
        "email": form_data.get("email", "").strip(),
        "password": form_data.get("password", ""),
    }
    if not all(values.values()):
        return values, "All fields are required."
    if not EMAIL_PATTERN.fullmatch(values["email"]):
        return values, "Enter a valid email address."
    if len(values["password"]) < 8:
        return values, "Password must be at least 8 characters long."
    return values, None


@bp.route("/")
def index():
    student = _get_authenticated_student()
    if student is None:
        return redirect(url_for("main.login"))
    return render_template("portal.html", student=student)


def _get_authenticated_student():
    """Return the logged-in student, or None when the session is invalid."""
    student_id = session.get("student_id")
    if student_id is None:
        return None
    return Student.query.filter_by(id=student_id).first()


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        values, error = _registration_values(request.form)
        if error:
            flash(error, "error")
            return render_template("register.html")

        duplicate = Student.query.filter(
            (Student.student_id == values["student_id"])
            | (Student.email == values["email"])
        ).first()
        if duplicate:
            flash("An account with that student ID or email already exists.", "error")
            return render_template("register.html")

        student = Student(
            student_id=values["student_id"],
            full_name=values["full_name"],
            email=values["email"],
            password_hash=generate_password_hash(values["password"]),
        )
        db.session.add(student)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("An account with that student ID or email already exists.", "error")
            return render_template("register.html")

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("main.login"))

    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        password = request.form.get("password", "")
        student = Student.query.filter_by(student_id=student_id).first()
        if student and check_password_hash(student.password_hash, password):
            session.clear()
            session["student_id"] = student.id
            flash("Login successful.", "success")
            return render_template("login.html", logged_in=True)
        flash("Invalid student ID or password.", "error")

    return render_template("login.html", logged_in=False)


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.login"))
