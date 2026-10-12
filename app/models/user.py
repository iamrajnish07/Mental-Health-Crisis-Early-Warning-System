from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_ref = Column(String(50), unique=True, index=True)  # Pseudonymous student/staff ref, e.g., STU-1001
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="student")  # 'student', 'counsellor', 'admin'
    department = Column(String(100), nullable=True)
    academic_year = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    consent = relationship("Consent", back_populates="user", uselist=False, cascade="all, delete-orphan")
    checkins = relationship("CheckIn", back_populates="user", cascade="all, delete-orphan")
    baseline = relationship("PersonalBaseline", back_populates="user", uselist=False, cascade="all, delete-orphan")
    assessments = relationship("RiskAssessment", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", foreign_keys="Alert.user_id", cascade="all, delete-orphan")
