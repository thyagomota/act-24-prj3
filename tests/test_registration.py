import pytest
from werkzeug.security import check_password_hash

from app.models import Student


def registration_data(**overrides):
    data = {
        "student_id": "student-123",
        "full_name": "Alex Student",
        "email": "alex@example.edu",
        "password": "securepass",
    }
    data.update(overrides)
    return data


def test_registration_creates_account_and_allows_login(client, app):
    response = client.post(
        "/register", data=registration_data(), follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Registration successful" in response.data
    with app.app_context():
        student = Student.query.filter_by(student_id="student-123").one()
        assert student.full_name == "Alex Student"
        assert student.email == "alex@example.edu"

    login_response = client.post(
        "/login",
        data={"student_id": "student-123", "password": "securepass"},
    )
    assert login_response.status_code == 200
    assert b"Login successful" in login_response.data
    with client.session_transaction() as session:
        assert session["student_id"]


@pytest.mark.parametrize(
    "missing_field", ["student_id", "full_name", "email", "password"]
)
def test_registration_rejects_missing_field(client, app, missing_field):
    data = registration_data()
    data.pop(missing_field)

    response = client.post("/register", data=data)

    assert b"All fields are required." in response.data
    with app.app_context():
        assert Student.query.count() == 0


def test_registration_rejects_malformed_email(client, app):
    response = client.post(
        "/register", data=registration_data(email="not-an-email")
    )

    assert b"Enter a valid email address." in response.data
    with app.app_context():
        assert Student.query.count() == 0


def test_registration_rejects_short_password(client, app):
    response = client.post(
        "/register", data=registration_data(password="short")
    )

    assert b"Password must be at least 8 characters long." in response.data
    with app.app_context():
        assert Student.query.count() == 0


def test_registration_rejects_duplicate_student_id(client, app):
    client.post("/register", data=registration_data())

    response = client.post(
        "/register", data=registration_data(email="other@example.edu")
    )

    assert b"student ID or email already exists" in response.data
    with app.app_context():
        assert Student.query.count() == 1


def test_registration_rejects_duplicate_email(client, app):
    client.post("/register", data=registration_data())

    response = client.post(
        "/register", data=registration_data(student_id="student-456")
    )

    assert b"student ID or email already exists" in response.data
    with app.app_context():
        assert Student.query.count() == 1


def test_registration_stores_password_hash_not_plaintext(client, app):
    password = "securepass"
    client.post("/register", data=registration_data(password=password))

    with app.app_context():
        student = Student.query.filter_by(student_id="student-123").one()
        assert student.password_hash != password
        assert check_password_hash(student.password_hash, password)


def test_login_rejects_invalid_password(client, app):
    client.post("/register", data=registration_data())

    response = client.post(
        "/login", data={"student_id": "student-123", "password": "wrongpass"}
    )

    assert b"Invalid student ID or password." in response.data
    with app.app_context():
        assert Student.query.count() == 1
