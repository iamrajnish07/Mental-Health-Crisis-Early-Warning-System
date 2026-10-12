from app.config import settings
from app.models.checkin import CheckIn, PersonalBaseline
from app.models.assessment import RiskAssessment
from app.security.authentication import create_session_token

def test_submit_checkin_success(client, student_user, db_session):
    token = create_session_token(student_user.id, student_user.role)
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)

    response = client.post("/student/checkin", data={
        "sleep_hours": 7.5,
        "sleep_quality": 8,
        "activity_level": 7,
        "mood_score": 8,
        "social_engagement": 7,
        "requested_counsellor": False,
        "optional_notes": "Felt productive today."
    }, follow_redirects=False)

    assert response.status_code == 303
    assert "/student/dashboard?submitted=true" in response.headers["location"]

    # Verify checkin was created
    checkin = db_session.query(CheckIn).filter(CheckIn.user_id == student_user.id).first()
    assert checkin is not None
    assert checkin.sleep_hours == 7.5

    # Verify assessment was generated
    assessment = db_session.query(RiskAssessment).filter(RiskAssessment.user_id == student_user.id).first()
    assert assessment is not None
    assert assessment.indicator_status in ["Stable", "Preliminary"]

def test_delete_personal_data_workflow(client, student_user, db_session):
    token = create_session_token(student_user.id, student_user.role)
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)

    # First add a checkin
    client.post("/student/checkin", data={
        "sleep_hours": 6.5,
        "sleep_quality": 7,
        "activity_level": 6,
        "requested_counsellor": False
    })

    # Trigger delete
    del_response = client.post("/student/delete-data", follow_redirects=False)
    assert del_response.status_code == 303

    # Assert records are permanently deleted
    remaining = db_session.query(CheckIn).filter(CheckIn.user_id == student_user.id).count()
    assert remaining == 0
