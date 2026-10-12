import json
from datetime import date
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.consent import Consent
from app.models.checkin import CheckIn, PersonalBaseline
from app.models.assessment import RiskAssessment
from app.security.authorization import require_student
from app.schemas.checkin import CheckInCreate
from app.services.checkin_service import submit_student_checkin
from app.security.audit import record_audit

router = APIRouter(prefix="/student", tags=["Student"])
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/dashboard", response_class=HTMLResponse)
def student_dashboard(
    request: Request,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    consent = db.query(Consent).filter(Consent.user_id == current_user.id).first()
    if not consent or not consent.general_consent:
        return RedirectResponse("/student/consent", status_code=302)

    # Fetch recent check-ins
    checkins = (
        db.query(CheckIn)
        .filter(CheckIn.user_id == current_user.id)
        .order_by(CheckIn.created_at.desc())
        .limit(14)
        .all()
    )

    # Prepare trend series for Chart.js (chronological order)
    chronological = list(reversed(checkins))
    labels = [c.checkin_date.strftime("%b %d") for c in chronological]
    sleep_series = [c.sleep_hours for c in chronological]
    activity_series = [c.activity_level for c in chronological]
    mood_series = [c.mood_score if c.mood_score else 0 for c in chronological]

    # Today's check-in status
    today_checkin = next((c for c in checkins if c.checkin_date == date.today()), None)

    # Latest assessment
    latest_assessment = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.user_id == current_user.id)
        .order_by(RiskAssessment.created_at.desc())
        .first()
    )

    baseline = db.query(PersonalBaseline).filter(PersonalBaseline.user_id == current_user.id).first()

    record_audit(db, "VIEW_DASHBOARD", "student_dashboard", user=current_user, request=request)

    return templates.TemplateResponse("student_dashboard.html", {
        "request": request,
        "user": current_user,
        "consent": consent,
        "today_checkin": today_checkin,
        "checkins": checkins,
        "latest_assessment": latest_assessment,
        "baseline": baseline,
        "chart_labels": json.dumps(labels),
        "chart_sleep": json.dumps(sleep_series),
        "chart_activity": json.dumps(activity_series),
        "chart_mood": json.dumps(mood_series)
    })

@router.get("/checkin", response_class=HTMLResponse)
def checkin_page(
    request: Request,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    consent = db.query(Consent).filter(Consent.user_id == current_user.id).first()
    if not consent or not consent.general_consent:
        return RedirectResponse("/student/consent", status_code=302)

    # Check if already submitted today
    today_checkin = (
        db.query(CheckIn)
        .filter(CheckIn.user_id == current_user.id, CheckIn.checkin_date == date.today())
        .first()
    )

    return templates.TemplateResponse("checkin.html", {
        "request": request,
        "user": current_user,
        "consent": consent,
        "today_checkin": today_checkin,
        "message": None,
        "error": None
    })

@router.post("/checkin")
def checkin_submit(
    request: Request,
    sleep_hours: float = Form(...),
    sleep_quality: int = Form(...),
    activity_level: int = Form(...),
    mood_score: int = Form(None),
    social_engagement: int = Form(None),
    requested_counsellor: bool = Form(False),
    optional_notes: str = Form(None),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    try:
        checkin_data = CheckInCreate(
            sleep_hours=sleep_hours,
            sleep_quality=sleep_quality,
            activity_level=activity_level,
            mood_score=mood_score,
            social_engagement=social_engagement,
            requested_counsellor=requested_counsellor,
            optional_notes=optional_notes
        )
        
        result = submit_student_checkin(db, current_user, checkin_data)
        record_audit(db, "SUBMIT_CHECKIN", "checkins", f"CheckIn id={result['checkin_id']}", user=current_user, request=request)
        return RedirectResponse("/student/dashboard?submitted=true", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        consent = db.query(Consent).filter(Consent.user_id == current_user.id).first()
        return templates.TemplateResponse("checkin.html", {
            "request": request,
            "user": current_user,
            "consent": consent,
            "today_checkin": None,
            "error": str(e)
        }, status_code=400)

@router.post("/delete-data")
def delete_student_data(
    request: Request,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Data privacy self-service: erase personal check-in records."""
    db.query(CheckIn).filter(CheckIn.user_id == current_user.id).delete()
    db.query(RiskAssessment).filter(RiskAssessment.user_id == current_user.id).delete()
    
    baseline = db.query(PersonalBaseline).filter(PersonalBaseline.user_id == current_user.id).first()
    if baseline:
        baseline.observation_count = 0
        baseline.avg_sleep_hours = 7.5
        baseline.avg_activity_level = 6.5
        
    record_audit(db, "DATA_DELETION_REQUEST", "student_records", "Student deleted personal wellbeing check-in records", user=current_user, request=request)
    db.commit()
    return RedirectResponse("/student/dashboard?deleted=true", status_code=status.HTTP_303_SEE_OTHER)
