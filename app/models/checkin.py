from datetime import datetime, date
from sqlalchemy import Column, Integer, Float, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class CheckIn(Base):
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    checkin_date = Column(Date, default=date.today, index=True)

    # Core reported dimensions
    sleep_hours = Column(Float, nullable=False)
    sleep_quality = Column(Integer, nullable=False)  # 1-10
    activity_level = Column(Integer, nullable=False) # 1-10
    mood_score = Column(Integer, nullable=True)      # 1-10 (optional)
    social_engagement = Column(Integer, nullable=True) # 1-10 (optional)
    
    # Direct support trigger
    requested_counsellor = Column(Boolean, default=False)
    optional_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="checkins")
    assessment = relationship("RiskAssessment", back_populates="checkin", uselist=False, cascade="all, delete-orphan")


class PersonalBaseline(Base):
    __tablename__ = "personal_baselines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    avg_sleep_hours = Column(Float, default=7.0)
    avg_sleep_quality = Column(Float, default=7.0)
    avg_activity_level = Column(Float, default=7.0)
    avg_mood_score = Column(Float, default=7.0)
    avg_social_engagement = Column(Float, default=7.0)
    observation_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="baseline")
