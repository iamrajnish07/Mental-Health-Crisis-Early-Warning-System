from datetime import date, datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.consent import Consent
from app.models.checkin import CheckIn, PersonalBaseline
from app.models.assessment import RiskAssessment
from app.models.alert import Alert
from app.schemas.checkin import CheckInCreate
from ml.feature_engineering import compute_deviations, update_baseline_metrics
from ml.predict import evaluate_checkin_risk

def submit_student_checkin(
    db: Session,
    student: User,
    data: CheckInCreate
) -> Dict[str, Any]:
    """Process a daily student check-in, compute baseline deviations, and evaluate risk indicators."""
    # Step 1: Verify student consent
    consent = db.query(Consent).filter(Consent.user_id == student.id).first()
    if not consent or not consent.general_consent or not consent.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active consent is required to submit wellbeing check-ins. Please review and accept the consent agreement."
        )

    # Step 2: Retrieve or initialize personal baseline
    baseline = db.query(PersonalBaseline).filter(PersonalBaseline.user_id == student.id).first()
    if not baseline:
        baseline = PersonalBaseline(
            user_id=student.id,
            avg_sleep_hours=data.sleep_hours,
            avg_sleep_quality=float(data.sleep_quality),
            avg_activity_level=float(data.activity_level),
            avg_mood_score=float(data.mood_score) if data.mood_score else 7.0,
            avg_social_engagement=float(data.social_engagement) if data.social_engagement else 7.0,
            observation_count=0
        )
        db.add(baseline)
        db.commit()
        db.refresh(baseline)

    baseline_dict = {
        "avg_sleep_hours": baseline.avg_sleep_hours,
        "avg_sleep_quality": baseline.avg_sleep_quality,
        "avg_activity_level": baseline.avg_activity_level,
        "avg_mood_score": baseline.avg_mood_score,
        "avg_social_engagement": baseline.avg_social_engagement,
        "observation_count": baseline.observation_count
    }

    # Step 3: Compute deviations
    deviations = compute_deviations(data.model_dump(), baseline_dict)

    # Step 4: Persist Check-In record
    checkin = CheckIn(
        user_id=student.id,
        checkin_date=date.today(),
        sleep_hours=data.sleep_hours,
        sleep_quality=data.sleep_quality,
        activity_level=data.activity_level,
        mood_score=data.mood_score if consent.consent_mood_tracking else None,
        social_engagement=data.social_engagement if consent.consent_social_tracking else None,
        requested_counsellor=data.requested_counsellor,
        optional_notes=data.optional_notes
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)

    # Step 5: Update baseline running metrics
    updated_metrics = update_baseline_metrics(baseline_dict, data.model_dump())
    baseline.avg_sleep_hours = updated_metrics["avg_sleep_hours"]
    baseline.avg_sleep_quality = updated_metrics["avg_sleep_quality"]
    baseline.avg_activity_level = updated_metrics["avg_activity_level"]
    baseline.avg_mood_score = updated_metrics["avg_mood_score"]
    baseline.avg_social_engagement = updated_metrics["avg_social_engagement"]
    baseline.observation_count = updated_metrics["observation_count"]
    baseline.last_updated = datetime.utcnow()
    db.commit()

    # Step 6: ML & Safety Rules Risk Assessment
    eval_payload = {
        **data.model_dump(),
        **deviations
    }
    assessment_result = evaluate_checkin_risk(eval_payload, baseline_dict)

    assessment = RiskAssessment(
        checkin_id=checkin.id,
        user_id=student.id,
        indicator_status=assessment_result["indicator_status"],
        model_version=assessment_result["model_version"],
        model_confidence=assessment_result["model_confidence"],
        sleep_deviation=deviations["sleep_deviation"],
        activity_deviation=deviations["activity_deviation"],
        mood_deviation=deviations["mood_deviation"],
        reason_codes="; ".join(assessment_result["reason_codes"]),
        requires_human_review=assessment_result["requires_human_review"]
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    # Step 7: Create counsellor alert queue item if review required and consented
    alert_created = None
    if assessment_result["requires_human_review"] and consent.consent_counsellor_review:
        alert_code = f"ALT-{1000 + checkin.id}"
        priority = "High" if data.requested_counsellor or assessment_result["indicator_status"] == "Elevated Concern" else "Medium"
        alert_reason = " | ".join(assessment_result["reason_codes"])
        
        alert = Alert(
            alert_code=alert_code,
            user_id=student.id,
            assessment_id=assessment.id,
            status="New",
            priority=priority,
            reason=alert_reason
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        alert_created = alert.alert_code

    return {
        "checkin_id": checkin.id,
        "indicator_status": assessment_result["indicator_status"],
        "confidence": assessment_result["model_confidence"],
        "reason_codes": assessment_result["reason_codes"],
        "requires_human_review": assessment_result["requires_human_review"],
        "deviations": deviations,
        "alert_code": alert_created
    }
