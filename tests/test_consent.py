from app.config import settings
from app.models.consent import Consent
from app.security.authentication import create_session_token

def test_view_consent_page(client, student_user):
    token = create_session_token(student_user.id, student_user.role)
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)

    response = client.get("/student/consent")
    assert response.status_code == 200
    assert "Wellbeing Data Consent & Privacy" in response.text

def test_withdraw_consent(client, student_user, db_session):
    token = create_session_token(student_user.id, student_user.role)
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)

    # Submit consent form with general_consent unchecked
    response = client.post("/student/consent", data={
        "general_consent": False
    }, follow_redirects=False)

    assert response.status_code == 303
    
    consent = db_session.query(Consent).filter(Consent.user_id == student_user.id).first()
    assert consent.general_consent is False
    assert consent.is_active is False
    assert consent.withdrawn_at is not None
