from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.alert import Alert, CounsellorNote
from app.models.user import User

def list_counsellor_alerts(
    db: Session,
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieve authorized alert queue items for counsellors, pseudonomously identified."""
    query = db.query(Alert)
    
    if status_filter and status_filter != "all":
        query = query.filter(Alert.status == status_filter)
    if priority_filter and priority_filter != "all":
        query = query.filter(Alert.priority == priority_filter)
        
    alerts = query.order_by(Alert.created_at.desc()).all()
    results = []
    
    for a in alerts:
        student = a.user
        results.append({
            "id": a.id,
            "alert_code": a.alert_code,
            "student_ref": student.user_ref if student else "ANON",
            "department": student.department if student else "N/A",
            "academic_year": student.academic_year if student else "N/A",
            "status": a.status,
            "priority": a.priority,
            "reason": a.reason,
            "created_at": a.created_at.strftime("%Y-%m-%d %H:%M"),
            "notes_count": len(a.notes)
        })
    return results

def get_alert_detail(db: Session, alert_id: int) -> Dict[str, Any]:
    """Retrieve detailed alert context including timeline and notes."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
        
    student = alert.user
    assessment = alert.assessment
    checkin = assessment.checkin if assessment else None
    
    notes = []
    for n in alert.notes:
        notes.append({
            "id": n.id,
            "counsellor": n.counsellor.full_name if n.counsellor else "Staff Counsellor",
            "note_text": n.note_text,
            "action_taken": n.action_taken,
            "created_at": n.created_at.strftime("%Y-%m-%d %H:%M")
        })
        
    return {
        "id": alert.id,
        "alert_code": alert.alert_code,
        "student_ref": student.user_ref if student else "ANON",
        "department": student.department,
        "academic_year": student.academic_year,
        "status": alert.status,
        "priority": alert.priority,
        "reason": alert.reason,
        "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M"),
        "assessment": {
            "indicator_status": assessment.indicator_status if assessment else "N/A",
            "model_confidence": assessment.model_confidence if assessment else 0.0,
            "sleep_deviation": assessment.sleep_deviation if assessment else 0.0,
            "activity_deviation": assessment.activity_deviation if assessment else 0.0,
            "reason_codes": assessment.reason_codes if assessment else ""
        } if assessment else None,
        "checkin_context": {
            "sleep_hours": checkin.sleep_hours if checkin else None,
            "sleep_quality": checkin.sleep_quality if checkin else None,
            "activity_level": checkin.activity_level if checkin else None,
            "requested_counsellor": checkin.requested_counsellor if checkin else False,
            "notes": checkin.optional_notes if checkin else None
        } if checkin else None,
        "notes": notes
    }

def update_alert_status_and_note(
    db: Session,
    alert_id: int,
    counsellor: User,
    new_status: str,
    note_text: Optional[str] = None,
    action_taken: Optional[str] = None
) -> Alert:
    """Update alert lifecycle status and append counsellor record."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
        
    alert.status = new_status
    
    if note_text:
        note = CounsellorNote(
            alert_id=alert.id,
            counsellor_id=counsellor.id,
            note_text=note_text,
            action_taken=action_taken or "Follow-up logged"
        )
        db.add(note)
        
    db.commit()
    db.refresh(alert)
    return alert
