"""
Pydantic schemas for request/response validation and MongoDB document shapes.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Auth ─────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = ""


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# ── Patient / Inference Record ───────────────────────────────
class InferenceRecord(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    patient_name: str = ""
    patient_id: str = ""
    image_filename: str
    image_base64: Optional[str] = None
    heatmap_base64: Optional[str] = None
    classification: str
    confidence: float
    all_probabilities: Optional[dict] = None
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class InferenceResponse(BaseModel):
    id: str
    image_filename: str
    image_base64: str
    heatmap_base64: str
    classification: str
    confidence: float
    all_probabilities: dict
    created_at: str


class HistoryResponse(BaseModel):
    total: int
    records: List[dict]


# ── Dashboard Stats ──────────────────────────────────────────
class DashboardStats(BaseModel):
    total_scans: int
    benign_count: int
    malignant_count: int
    recent_scans: List[dict]
