import sys
from pathlib import Path
from datetime import date, datetime, timedelta

# Add workspace root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import engine, SessionLocal, Base
from app.models.user import User
from app.models.consent import Consent
from app.models.checkin import CheckIn, PersonalBaseline
from app.models.assessment import RiskAssessment
from app.models.alert import Alert, CounsellorNote, AuditLog
from app.security.authentication import hash_password
from ml.predict import evaluate_checkin_risk

def seed_database():
    """Seed initial development and demonstration data with realistic synthetic profiles."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("Checking existing database users...")
        existing_student = db.query(User).filter(User.email == "student@campus.edu").first()
        if existing_student:
            print("Demo accounts already present. Seeding skipped.")
            return

        print("Seeding demo accounts...")
        
        # 1. Student User
        student = User(
            user_ref="STU-1001",
            email="student@campus.edu",
            full_name="Alex Rivera",
            hashed_password=hash_password("StudentPass123!"),
            role="student",
            department="Computer Science",
            academic_year="3rd Year",
            is_active=True
        )
        
        # 2. Second Student User (to demonstrate alerts in queue)
        student2 = User(
            user_ref="STU-1002",
            email="priya@campus.edu",
            full_name="Priya Sharma",
            hashed_password=hash_password("StudentPass123!"),
            role="student",
            department="Electrical Engineering",
            academic_year="2nd Year",
            is_active=True
        )

        # 3. Counsellor User
        counsellor = User(
            user_ref="CNS-2001",
            email="counsellor@campus.edu",
            full_name="Dr. Sarah Jenkins",
            hashed_password=hash_password("CounsellorPass123!"),
            role="counsellor",
            department="Student Health & Counselling",
            academic_year="Staff",
            is_active=True
        )

        # 4. Administrator User
        admin = User(
            user_ref="ADM-3001",
            email="admin@campus.edu",
            full_name="Campus Dean Office",
            hashed_password=hash_password("AdminPass123!"),
            role="admin",
            department="University Administration",
            academic_year="Faculty",
            is_active=True
        )

        db.add_all([student, student2, counsellor, admin])
        db.commit()
        db.refresh(student)
        db.refresh(student2)
        db.refresh(counsellor)
        db.refresh(admin)

        # Consents
        consent1 = Consent(
            user_id=student.id,
            general_consent=True,
            consent_sleep_tracking=True,
            consent_activity_tracking=True,
            consent_mood_tracking=True,
            consent_social_tracking=True,
            consent_counsellor_review=True,
            consented_at=datetime.utcnow() - timedelta(days=10)
        )
        consent2 = Consent(
            user_id=student2.id,
            general_consent=True,
            consent_sleep_tracking=True,
            consent_activity_tracking=True,
            consent_mood_tracking=True,
            consent_social_tracking=True,
            consent_counsellor_review=True,
            consented_at=datetime.utcnow() - timedelta(days=5)
        )
        db.add_all([consent1, consent2])

        # Personal Baselines
        base1 = PersonalBaseline(
            user_id=student.id,
            avg_sleep_hours=7.5,
            avg_sleep_quality=7.4,
            avg_activity_level=6.8,
            avg_mood_score=7.0,
            avg_social_engagement=6.8,
            observation_count=7
        )
        base2 = PersonalBaseline(
            user_id=student2.id,
            avg_sleep_hours=7.2,
            avg_sleep_quality=6.8,
            avg_activity_level=6.5,
            avg_mood_score=6.0,
            avg_social_engagement=6.0,
            observation_count=4
        )
        db.add_all([base1, base2])
        db.commit()

        # Seed 7 days of historical check-ins for student 1
        today = date.today()
        historical_checkins = [
            (today - timedelta(days=6), 7.8, 8, 7, 8, 7, False),
            (today - timedelta(days=5), 7.5, 7, 7, 7, 7, False),
            (today - timedelta(days=4), 7.2, 7, 6, 7, 6, False),
            (today - timedelta(days=3), 7.0, 7, 7, 6, 6, False),
            (today - timedelta(days=2), 6.5, 6, 6, 6, 5, False),
            (today - timedelta(days=1), 7.0, 7, 6, 7, 7, False),
        ]
        
        for chk_date, sleep, sleep_q, act, mood, soc, req_cns in historical_checkins:
            chk = CheckIn(
                user_id=student.id,
                checkin_date=chk_date,
                sleep_hours=sleep,
                sleep_quality=sleep_q,
                activity_level=act,
                mood_score=mood,
                social_engagement=soc,
                requested_counsellor=req_cns,
                created_at=datetime.combine(chk_date, datetime.min.time())
            )
            db.add(chk)
            db.commit()
            db.refresh(chk)

            # Assessment
            assessment = RiskAssessment(
                checkin_id=chk.id,
                user_id=student.id,
                indicator_status="Stable",
                model_version="v1.0-simulated-rf",
                model_confidence=0.15,
                sleep_deviation=round(sleep - 7.5, 2),
                activity_deviation=round(act - 6.8, 2),
                reason_codes="wellbeing_indicators_within_typical_baseline",
                requires_human_review=False
            )
            db.add(assessment)
            db.commit()

        # Seed checkin for student 2 with habit shift to populate counsellor alert queue
        alert_chk = CheckIn(
            user_id=student2.id,
            checkin_date=today,
            sleep_hours=3.5,
            sleep_quality=3,
            activity_level=2,
            mood_score=3,
            social_engagement=2,
            requested_counsellor=True,
            optional_notes="Feeling overwhelmed with final year project deadlines",
            created_at=datetime.utcnow()
        )
        db.add(alert_chk)
        db.commit()
        db.refresh(alert_chk)

        alert_assessment = RiskAssessment(
            checkin_id=alert_chk.id,
            user_id=student2.id,
            indicator_status="Elevated Concern",
            model_version="v1.0-simulated-rf",
            model_confidence=0.88,
            sleep_deviation=-3.7,
            activity_deviation=-4.5,
            reason_codes="acute_sleep_duration_under_5_hours; significant_activity_drop; student_explicitly_requested_counsellor",
            requires_human_review=True
        )
        db.add(alert_assessment)
        db.commit()
        db.refresh(alert_assessment)

        alert = Alert(
            alert_code="ALT-1001",
            user_id=student2.id,
            assessment_id=alert_assessment.id,
            status="New",
            priority="High",
            reason="Acute sleep deficit (3.5h) | Student requested counsellor | Significant activity drop"
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        # Audit logs
        db.add(AuditLog(
            user_id=admin.id,
            user_role="admin",
            action="SYSTEM_INIT",
            resource="database",
            details="System seeded with initial university profiles"
        ))
        db.commit()

        print("Demo database successfully seeded!")
        print("  - Student:    student@campus.edu    / StudentPass123!")
        print("  - Counsellor: counsellor@campus.edu / CounsellorPass123!")
        print("  - Admin:      admin@campus.edu      / AdminPass123!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
