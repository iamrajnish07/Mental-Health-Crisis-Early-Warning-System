from typing import Optional
from fastapi import Request
from sqlalchemy.orm import Session
from app.models.alert import AuditLog
from app.models.user import User

def record_audit(
    db: Session,
    action: str,
    resource: str,
    details: Optional[str] = None,
    user: Optional[User] = None,
    request: Optional[Request] = None
):
    """Log security-relevant application events without capturing sensitive personal data."""
    ip_addr = None
    if request:
        ip_addr = request.client.host if request.client else "unknown"
        
    log_entry = AuditLog(
        user_id=user.id if user else None,
        user_role=user.role if user else "anonymous",
        action=action,
        resource=resource,
        details=details[:250] if details else None,
        ip_address=ip_addr
    )
    db.add(log_entry)
    db.commit()
