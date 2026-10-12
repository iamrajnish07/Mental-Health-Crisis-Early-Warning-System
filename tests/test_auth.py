from app.config import settings
from app.security.authentication import create_session_token

def test_health_check_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"

def test_login_success_and_cookie(client, student_user):
    response = client.post("/login", data={
        "email": "test_student@campus.edu",
        "password": "Password123!"
    }, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/student/dashboard"
    assert settings.SESSION_COOKIE_NAME in response.cookies

def test_login_invalid_password(client, student_user):
    response = client.post("/login", data={
        "email": "test_student@campus.edu",
        "password": "WrongPassword!"
    })
    assert response.status_code == 400
    assert "Invalid email or password" in response.text

def test_student_registration(client):
    response = client.post("/register", data={
        "full_name": "New Enrolled Student",
        "email": "new_student@campus.edu",
        "password": "SecurePassword123!",
        "role": "student",
        "department": "Biotechnology",
        "academic_year": "1st Year"
    }, follow_redirects=False)

    assert response.status_code == 303
    assert settings.SESSION_COOKIE_NAME in response.cookies
