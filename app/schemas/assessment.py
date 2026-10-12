from typing import List, Optional
from pydantic import BaseModel

class RiskAssessmentResponse(BaseModel):
    id: int
    indicator_status: str
    model_version: str
    model_confidence: float
    sleep_deviation: float
    activity_deviation: float
    reason_codes: List[str]
    requires_human_review: bool

class AlertStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None
    action_taken: Optional[str] = None
