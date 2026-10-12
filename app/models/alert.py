from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_code = Column(String(50), unique=True, index=True) # ALT-1001
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(Integer, ForeignKey("risk_assessments.id", ondelete="CASCADE"), nullable=True)

    # Statuses: 'New', 'Pending Review', 'Contact Initiated', 'Follow-up Required', 'Resolved', 'Closed'
    status = Column(String(50), default="New", index=True)
    priority = Column(String(20), default="Medium") # 'Low', 'Medium', 'High'
    reason = Column(Text, nullable=False)
    
    # Audit timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="alerts", foreign_keys=[user_id])
    assessment = relationship("RiskAssessment", back_populates="alert")
    notes = relationship("CounsellorNote", back_populates="alert", cascade="all, delete-orphan")


class CounsellorNote(Base):
    __tablename__ = "counsellor_notes"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    counsellor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    note_text = Column(Text, nullable=False)
    action_taken = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    alert = relationship("Alert", back_populates="notes")
    counsellor = relationship("User", foreign_keys=[counsellor_id])


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    user_role = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False) # e.g. "VIEW_CHECKIN", "UPDATE_ALERT_STATUS"
    resource = Column(String(100), nullable=True)
    details = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
