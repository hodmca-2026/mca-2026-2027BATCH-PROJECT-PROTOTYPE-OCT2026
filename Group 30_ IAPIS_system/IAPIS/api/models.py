"""
API Request/Response Models (Pydantic)

Defines the contracts for the FastAPI endpoints as specified in the build spec.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    """Request body for /search and /analyze endpoints."""
    query: str = Field(..., description="Natural language safety query")
    top_k: int = Field(5, ge=1, le=20, description="Number of results to return")
    alpha: float = Field(0.5, ge=0.0, le=1.0, description="Dense vs BM25 weight (higher = more dense)")


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------
class ReportResult(BaseModel):
    """A single report result in the search response."""
    id: str
    title: str = ""
    snippet: str = ""
    dense_score: float = 0.0
    bm25_score: float = 0.0
    rerank_score: float = 0.0
    recurrence_score: float = 0.0
    equipment: str = ""
    hazard_type: str = ""
    severity: str = ""
    location: str = ""
    date: str = ""
    source: str = ""


class EquipmentFlag(BaseModel):
    """Risk flags for a single equipment unit."""
    lstm_drift_risk: float = 0.0
    flag: bool = False
    autoencoder_anomaly: bool = False


class RiskSummary(BaseModel):
    """Risk summary including equipment flags and recurrence pattern."""
    equipment_flags: Dict[str, EquipmentFlag] = {}
    recurrence_pattern: str = ""


class SearchResponse(BaseModel):
    """Response for /search endpoint."""
    results: List[ReportResult] = []


class AnalyzeResponse(BaseModel):
    """Response for /analyze endpoint."""
    results: List[ReportResult] = []
    risk_summary: RiskSummary = RiskSummary()
    recommendation: str = ""
    llm_provider: str = ""


class PPEDetection(BaseModel):
    """A single PPE detection result."""
    class_name: str
    confidence: float
    bbox: List[float] = []  # [x1, y1, x2, y2]


class PPEResponse(BaseModel):
    """Response for /detect-ppe endpoint."""
    detections: List[PPEDetection] = []
    message: str = ""


class HealthResponse(BaseModel):
    """Response for /health endpoint."""
    status: str = "ok"
