from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.consent import Consent
from app.models.checkin import PersonalBaseline
from app.security.authentication import (
    hash_password,
    verify_password,
    create_session_token,
    get_current_user_optional
)
from app.security.audit import record_audit

router = APIRouter(tags=["Authentication"])
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db)
    if current_user:
        if current_user.role == "student":
            return RedirectResponse("/student/dashboard", status_code=302)
        elif current_user.role == "counsellor":
            return RedirectResponse("/counsellor/dashboard", status_code=302)
        elif current_user.role == "admin":
            return RedirectResponse("/admin/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login")
def login_post(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid email or password. Please try again."
        }, status_code=400)

    if not user.is_active:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "This account is inactive. Please contact administration."
        }, status_code=403)

    token = create_session_token(user.id, user.role)
    record_audit(db, "LOGIN_SUCCESS", "auth", f"User {user.email} logged in", user=user, request=request)

    # Determine destination
    dest = "/student/dashboard"
    if user.role == "counsellor":
        dest = "/counsellor/dashboard"
    elif user.role == "admin":
        dest = "/admin/dashboard"

    redirect = RedirectResponse(dest, status_code=status.HTTP_303_SEE_OTHER)
    redirect.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False # Set to True in HTTPS production
    )
    return redirect

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db)
    if current_user:
        return RedirectResponse("/student/dashboard", status_code=302)
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@router.post("/register")
def register_post(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("student"),
    department: str = Form("Computer Science"),
    academic_year: str = Form("3rd Year"),
    db: Session = Depends(get_db)
):
    clean_email = email.strip().lower()
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "An account with this email address is already registered."
        }, status_code=400)

    if len(password) < 6:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Password must be at least 6 characters long."
        }, status_code=400)

    # Generate pseudo ref
    user_count = db.query(User).count()
    prefix = "STU" if role == "student" else ("CNS" if role == "counsellor" else "ADM")
    user_ref = f"{prefix}-{1001 + user_count}"

    new_user = User(
        user_ref=user_ref,
        email=clean_email,
        full_name=full_name.strip(),
        hashed_password=hash_password(password),
        role=role,
        department=department.strip(),
        academic_year=academic_year.strip(),
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # If student, initialize consent template & baseline
    if role == "student":
        consent = Consent(
            user_id=new_user.id,
            general_consent=False,
            consent_sleep_tracking=True,
            consent_activity_tracking=True,
            consent_mood_tracking=True,
            consent_social_tracking=True,
            consent_counsellor_review=True
        )
        baseline = PersonalBaseline(
            user_id=new_user.id,
            avg_sleep_hours=7.5,
            avg_sleep_quality=7.0,
            avg_activity_level=6.5,
            avg_mood_score=6.5,
            avg_social_engagement=6.5,
            observation_count=0
        )
        db.add(consent)
        db.add(baseline)
        db.commit()

    record_audit(db, "REGISTER_SUCCESS", "auth", f"User {new_user.email} created as {role}", user=new_user, request=request)

    # Log user in directly
    token = create_session_token(new_user.id, new_user.role)
    dest = "/student/consent" if role == "student" else ("/counsellor/dashboard" if role == "counsellor" else "/admin/dashboard")

    redirect = RedirectResponse(dest, status_code=status.HTTP_303_SEE_OTHER)
    redirect.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False
    )
    return redirect

@router.get("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db)
    if current_user:
        record_audit(db, "LOGOUT", "auth", f"User {current_user.email} logged out", user=current_user, request=request)
    redirect = RedirectResponse("/login", status_code=302)
    redirect.delete_cookie(settings.SESSION_COOKIE_NAME)
    return redirect
