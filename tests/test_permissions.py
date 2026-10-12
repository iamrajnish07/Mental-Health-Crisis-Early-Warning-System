from app.config import settings
from app.security.authentication import create_session_token

def test_unauthorized_access_redirects_or_rejects(client):
    response = client.get("/student/dashboard", follow_redirects=False)
    assert response.status_code == 401

def test_student_cannot_access_counsellor_dashboard(client, student_user):
    token = create_session_token(student_user.id, student_user.role)
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)

    response = client.get("/counsellor/dashboard")
    assert response.status_code == 403
    assert "Access denied" in response.text

def test_counsellor_cannot_access_admin_dashboard(client, counsellor_user):
    token = create_session_token(counsellor_user.id, counsellor_user.role)
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)

    response = client.get("/admin/dashboard")
    assert response.status_code == 403

def test_admin_can_access_admin_dashboard(client, admin_user):
    token = create_session_token(admin_user.id, admin_user.role)
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)

    response = client.get("/admin/dashboard")
    assert response.status_code == 200
    assert "Campus Administration" in response.text
