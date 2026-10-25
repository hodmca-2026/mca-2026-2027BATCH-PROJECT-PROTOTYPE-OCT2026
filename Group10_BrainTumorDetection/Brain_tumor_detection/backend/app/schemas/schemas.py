from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, EmailStr, Field


# ---- Auth ----
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=6)
    role: str = Field(description="doctor | researcher | admin")


class UserOut(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---- Cases ----
class CaseCreate(BaseModel):
    patient_ref_id: str


class CaseOut(BaseModel):
    id: str
    case_code: str
    patient_ref_id: str
    status: str
    created_at: datetime
    latest_class: Optional[str] = None
    latest_confidence: Optional[float] = None
    latest_prediction_id: Optional[str] = None
    symptom_level: Optional[str] = None

    class Config:
        from_attributes = True


# ---- Predictions ----
class PredictionOut(BaseModel):
    id: str
    case_id: str
    predicted_class: str
    confidence_score: float
    all_class_probabilities: Dict[str, float]
    original_url: Optional[str] = None
    heatmap_url: Optional[str] = None
    overlay_url: Optional[str] = None
    disclaimer: str
    model_version: str
    predicted_at: datetime

    class Config:
        from_attributes = True


# ---- Reports ----
class ReportGenerateRequest(BaseModel):
    prediction_id: str


class ReportOut(BaseModel):
    id: str
    case_id: str
    prediction_id: str
    draft_content: str
    reviewed_content: Optional[str]
    review_status: str
    is_ai_generated: bool
    generated_at: datetime

    class Config:
        from_attributes = True


class ReportReviewRequest(BaseModel):
    reviewed_content: str
    approve: bool = False
