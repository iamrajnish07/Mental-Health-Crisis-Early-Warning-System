from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.checkin import CheckIn
from app.models.assessment import RiskAssessment
from app.models.alert import Alert, AuditLog
from app.config import settings
from ml.predict import get_model_metadata

def get_privacy_preserving_admin_metrics(db: Session) -> Dict[str, Any]:
    """Calculate aggregated university-level metrics with small-group privacy suppression."""
    min_k = settings.MIN_GROUP_SIZE_FOR_ADMIN_METRICS
    
    total_students = db.query(User).filter(User.role == "student", User.is_active == True).count()
    total_counsellors = db.query(User).filter(User.role == "counsellor", User.is_active == True).count()
    
    # Active check-ins past 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    total_checkins = db.query(CheckIn).count()
    recent_checkins = db.query(CheckIn).filter(CheckIn.created_at >= thirty_days_ago).count()
    
    # Active participants (unique students check-in within last 30 days)
    active_students_count = db.query(func.count(func.distinct(CheckIn.user_id))).filter(
        CheckIn.created_at >= thirty_days_ago
    ).scalar() or 0
    
    # Aggregated indicator distribution (Privacy k-anonymity check)
    assessments_summary = db.query(
        RiskAssessment.indicator_status,
        func.count(RiskAssessment.id)
    ).group_by(RiskAssessment.indicator_status).all()
    
    status_distribution = {}
    for st, count in assessments_summary:
        # If count < min_k, suppress or mask to protect privacy
        status_distribution[st] = count if count >= min_k else f"< {min_k} (Suppressed)"
        
    # Total alert stats
    total_alerts = db.query(Alert).count()
    active_alerts = db.query(Alert).filter(Alert.status.in_(["New", "Pending Review", "Contact Initiated", "Follow-up Required"])).count()
    resolved_alerts = db.query(Alert).filter(Alert.status.in_(["Resolved", "Closed"])).count()
    
    # Participation rate
    participation_rate = round((active_students_count / total_students * 100), 1) if total_students > 0 else 0.0

    # Model metadata
    ml_meta = get_model_metadata()

    # Recent security audit events
    recent_audits = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
    audit_list = [{
        "timestamp": a.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "role": a.user_role or "system",
        "action": a.action,
        "resource": a.resource,
        "details": a.details
    } for a in recent_audits]

    return {
        "k_suppression_threshold": min_k,
        "total_students": total_students,
        "total_counsellors": total_counsellors,
        "active_students_30d": active_students_count,
        "participation_rate_percent": participation_rate,
        "total_checkins": total_checkins,
        "recent_checkins_30d": recent_checkins,
        "indicator_distribution": status_distribution,
        "alert_stats": {
            "total": total_alerts,
            "active": active_alerts,
            "resolved": resolved_alerts
        },
        "model_metadata": ml_meta,
        "recent_audit_logs": audit_list
    }
