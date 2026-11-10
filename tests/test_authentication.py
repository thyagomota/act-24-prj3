from app.models import Student


def register_student(client):
    return client.post(
        "/register",
        data={
            "student_id": "student-123",
            "full_name": "Alex Student",
            "email": "alex@example.edu",
            "password": "securepass",
        },
    )


def test_valid_login_grants_access_to_protected_portal(client):
    register_student(client)

    response = client.post(
        "/login",
        data={"student_id": "student-123", "password": "securepass"},
    )

    assert response.status_code == 200
    assert b"Login successful." in response.data
    with client.session_transaction() as session:
        assert session["student_id"]

    portal_response = client.get("/")
    assert portal_response.status_code == 200
    assert b"Welcome, Alex Student" in portal_response.data


def test_invalid_login_shows_error_without_authenticating(client, app):
    register_student(client)

    response = client.post(
        "/login",
        data={"student_id": "student-123", "password": "incorrect"},
    )

    assert b"Invalid student ID or password." in response.data
    with client.session_transaction() as session:
        assert "student_id" not in session
    with app.app_context():
        assert Student.query.count() == 1


def test_protected_portal_redirects_unauthenticated_student(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    assert b"Welcome, Alex Student" not in response.data


def test_logout_terminates_protected_access(client):
    register_student(client)
    client.post(
        "/login",
        data={"student_id": "student-123", "password": "securepass"},
    )

    logout_response = client.post("/logout")

    assert logout_response.status_code == 302
    with client.session_transaction() as session:
        assert "student_id" not in session

    portal_response = client.get("/")
    assert portal_response.status_code == 302
    assert portal_response.headers["Location"].endswith("/login")
