from pathlib import Path
from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.security.authorization import require_admin
from app.services.analytics_service import get_privacy_preserving_admin_metrics
from app.security.audit import record_audit

router = APIRouter(prefix="/admin", tags=["Administrator"])
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/dashboard", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    metrics = get_privacy_preserving_admin_metrics(db)
    users = db.query(User).order_by(User.created_at.desc()).limit(50).all()

    record_audit(db, "VIEW_ADMIN_DASHBOARD", "admin_dashboard", user=current_user, request=request)

    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "user": current_user,
        "metrics": metrics,
        "users": users
    })

@router.post("/user/{user_id}/toggle-status")
def toggle_user_active_status(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if target_user and target_user.id != current_user.id:
        target_user.is_active = not target_user.is_active
        db.commit()
        record_audit(db, "TOGGLE_USER_STATUS", f"user_{user_id}", f"Set active={target_user.is_active}", user=current_user, request=request)
    return RedirectResponse("/admin/dashboard?updated=true", status_code=status.HTTP_303_SEE_OTHER)
