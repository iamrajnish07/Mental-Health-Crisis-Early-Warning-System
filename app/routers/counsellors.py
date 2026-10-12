from pathlib import Path
from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.security.authorization import require_counsellor
from app.services.alert_service import (
    list_counsellor_alerts,
    get_alert_detail,
    update_alert_status_and_note
)
from app.security.audit import record_audit

router = APIRouter(prefix="/counsellor", tags=["Counsellor"])
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/dashboard", response_class=HTMLResponse)
def counsellor_dashboard(
    request: Request,
    status_filter: str = "all",
    priority_filter: str = "all",
    current_user: User = Depends(require_counsellor),
    db: Session = Depends(get_db)
):
    alerts = list_counsellor_alerts(db, status_filter, priority_filter)
    
    # Counts by status
    total_new = sum(1 for a in alerts if a["status"] == "New")
    total_pending = sum(1 for a in alerts if a["status"] in ["Pending Review", "Contact Initiated", "Follow-up Required"])
    total_resolved = sum(1 for a in alerts if a["status"] in ["Resolved", "Closed"])

    record_audit(db, "VIEW_COUNSELLOR_QUEUE", "alerts_queue", user=current_user, request=request)

    return templates.TemplateResponse("counsellor_dashboard.html", {
        "request": request,
        "user": current_user,
        "alerts": alerts,
        "total_new": total_new,
        "total_pending": total_pending,
        "total_resolved": total_resolved,
        "current_status": status_filter,
        "current_priority": priority_filter
    })

@router.get("/alert/{alert_id}", response_class=HTMLResponse)
def view_alert_details(
    alert_id: int,
    request: Request,
    current_user: User = Depends(require_counsellor),
    db: Session = Depends(get_db)
):
    alert_data = get_alert_detail(db, alert_id)
    record_audit(db, "VIEW_ALERT_DETAIL", f"alert_{alert_id}", user=current_user, request=request)
    return templates.TemplateResponse("alert_detail.html", {
        "request": request,
        "user": current_user,
        "alert": alert_data
    })

@router.post("/alert/{alert_id}/update")
def update_alert(
    alert_id: int,
    request: Request,
    new_status: str = Form(...),
    note_text: str = Form(None),
    action_taken: str = Form(None),
    current_user: User = Depends(require_counsellor),
    db: Session = Depends(get_db)
):
    update_alert_status_and_note(
        db=db,
        alert_id=alert_id,
        counsellor=current_user,
        new_status=new_status,
        note_text=note_text,
        action_taken=action_taken
    )
    record_audit(db, "UPDATE_ALERT_RECORD", f"alert_{alert_id}", f"Status changed to {new_status}", user=current_user, request=request)
    return RedirectResponse(f"/counsellor/dashboard?updated=true", status_code=status.HTTP_303_SEE_OTHER)
