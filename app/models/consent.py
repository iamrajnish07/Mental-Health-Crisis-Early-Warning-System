from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Consent(Base):
    __tablename__ = "consents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Granular consent scopes
    general_consent = Column(Boolean, default=False)
    consent_sleep_tracking = Column(Boolean, default=False)
    consent_activity_tracking = Column(Boolean, default=False)
    consent_mood_tracking = Column(Boolean, default=False)
    consent_social_tracking = Column(Boolean, default=False)
    consent_counsellor_review = Column(Boolean, default=False)
    
    consented_at = Column(DateTime, default=datetime.utcnow)
    withdrawn_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    version = Column(String(20), default="1.0")
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="consent")
