from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.consent import Consent
from app.security.authorization import require_student
from app.security.audit import record_audit

router = APIRouter(prefix="/student", tags=["Consent"])
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/consent", response_class=HTMLResponse)
def consent_page(
    request: Request,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    consent = db.query(Consent).filter(Consent.user_id == current_user.id).first()
    return templates.TemplateResponse("consent.html", {
        "request": request,
        "user": current_user,
        "consent": consent,
        "saved": request.query_params.get("saved")
    })

@router.post("/consent")
def update_consent(
    request: Request,
    general_consent: bool = Form(False),
    consent_sleep_tracking: bool = Form(False),
    consent_activity_tracking: bool = Form(False),
    consent_mood_tracking: bool = Form(False),
    consent_social_tracking: bool = Form(False),
    consent_counsellor_review: bool = Form(False),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    consent = db.query(Consent).filter(Consent.user_id == current_user.id).first()
    if not consent:
        consent = Consent(user_id=current_user.id)
        db.add(consent)

    previous_consent = consent.general_consent
    consent.general_consent = general_consent
    consent.consent_sleep_tracking = consent_sleep_tracking
    consent.consent_activity_tracking = consent_activity_tracking
    consent.consent_mood_tracking = consent_mood_tracking
    consent.consent_social_tracking = consent_social_tracking
    consent.consent_counsellor_review = consent_counsellor_review
    
    if general_consent and not previous_consent:
        consent.consented_at = datetime.utcnow()
        consent.withdrawn_at = None
        consent.is_active = True
        record_audit(db, "CONSENT_GRANTED", "consent", "Student accepted terms", user=current_user, request=request)
    elif not general_consent and previous_consent:
        consent.withdrawn_at = datetime.utcnow()
        consent.is_active = False
        record_audit(db, "CONSENT_WITHDRAWN", "consent", "Student withdrew consent", user=current_user, request=request)

    db.commit()

    if general_consent:
        return RedirectResponse("/student/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return RedirectResponse("/student/consent?saved=withdrawn", status_code=status.HTTP_303_SEE_OTHER)
