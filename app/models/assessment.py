from datetime import datetime
from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from app.database import Base

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    checkin_id = Column(Integer, ForeignKey("checkins.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Indicator status: 'Stable', 'Preliminary', 'Needs Review', 'Elevated Concern'
    indicator_status = Column(String(50), default="Stable")
    model_version = Column(String(50), default="v1.0-simulated-rf")
    model_confidence = Column(Float, default=0.0)
    
    # Deviations from personal baseline
    sleep_deviation = Column(Float, default=0.0)
    activity_deviation = Column(Float, default=0.0)
    mood_deviation = Column(Float, default=0.0)

    # JSON or semicolon string of reason codes (e.g. "change_in_sleep_pattern;change_in_activity_level")
    reason_codes = Column(Text, default="")
    
    # Human-in-the-loop requirement
    requires_human_review = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="assessments")
    checkin = relationship("CheckIn", back_populates="assessment")
    alert = relationship("Alert", back_populates="assessment", uselist=False, cascade="all, delete-orphan")
