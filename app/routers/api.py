from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.config import settings
from app.models.user import User
from app.security.authentication import get_current_user
from app.security.authorization import require_admin
from app.services.analytics_service import get_privacy_preserving_admin_metrics
from ml.predict import get_model_metadata

router = APIRouter(prefix="/api", tags=["API"])

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint validating database connectivity and system status."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database": db_status
    }

@router.get("/model/metadata")
def model_metadata():
    """Retrieve machine learning model metadata, training configuration, and evaluation statistics."""
    return get_model_metadata()

@router.get("/admin/metrics")
def admin_metrics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Programmatic privacy-preserving metrics endpoint for authorized administrators."""
    return get_privacy_preserving_admin_metrics(db)
