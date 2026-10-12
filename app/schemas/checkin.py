from typing import Optional
from pydantic import BaseModel, Field

class ConsentUpdate(BaseModel):
    general_consent: bool
    consent_sleep_tracking: bool = True
    consent_activity_tracking: bool = True
    consent_mood_tracking: bool = True
    consent_social_tracking: bool = True
    consent_counsellor_review: bool = True

class CheckInCreate(BaseModel):
    sleep_hours: float = Field(..., ge=0.0, le=24.0, description="Reported hours of sleep")
    sleep_quality: int = Field(..., ge=1, le=10, description="Rated 1 to 10")
    activity_level: int = Field(..., ge=1, le=10, description="Rated 1 to 10")
    mood_score: Optional[int] = Field(None, ge=1, le=10, description="Optional rated 1 to 10")
    social_engagement: Optional[int] = Field(None, ge=1, le=10, description="Optional rated 1 to 10")
    requested_counsellor: bool = False
    optional_notes: Optional[str] = Field(None, max_length=500)

class CheckInResponse(BaseModel):
    id: int
    user_id: int
    checkin_date: str
    sleep_hours: float
    sleep_quality: int
    activity_level: int
    mood_score: Optional[int]
    social_engagement: Optional[int]
    requested_counsellor: bool

    class Config:
        from_attributes = True
