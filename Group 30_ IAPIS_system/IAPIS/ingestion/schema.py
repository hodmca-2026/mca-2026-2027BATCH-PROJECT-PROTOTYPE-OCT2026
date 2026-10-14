"""
Pydantic data models for the IAPIS report schema.
Matches schema 5.1 from the build specification.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class Report(BaseModel):
    """
    Schema for a single incident/near-miss/maintenance report.
    
    Required fields: id, type, title, text
    Optional fields are populated by NER if missing from source data.
    """
    id: str = Field(..., description="Unique report identifier, e.g. RPT-0001")
    type: Literal["accident", "near_miss", "maintenance_log"] = Field(
        ..., description="Report type"
    )
    title: str = Field(..., description="Short descriptive title")
    text: str = Field(..., description="Full free-text narrative")
    equipment: Optional[str] = Field(
        None, description="Equipment involved, e.g. 'induction motor'"
    )
    hazard_type: Optional[str] = Field(
        None, description="Primary hazard type, e.g. 'overheating'"
    )
    location: Optional[str] = Field(
        None, description="Location of the incident"
    )
    date: Optional[str] = Field(
        None, description="Date of the incident (YYYY-MM-DD)"
    )
    severity: Optional[Literal["low", "medium", "high", "critical"]] = Field(
        None, description="Severity classification"
    )
    source: Optional[Literal["synthetic", "osha"]] = Field(
        "synthetic", description="Data source"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "RPT-0001",
                "type": "accident",
                "title": "Motor M-12 overheating causing smoke event",
                "text": "Full free-text narrative of what happened...",
                "equipment": "induction motor",
                "hazard_type": "overheating",
                "location": "Building 3, Line 2",
                "date": "2024-03-14",
                "severity": "medium",
                "source": "synthetic",
            }
        }


class SensorReading(BaseModel):
    """Schema for a single row in sensor_logs.csv."""
    timestamp: str
    equipment_id: str
    temperature_c: float
    vibration_mm_s: float
    rpm: float


class MaintenanceLog(BaseModel):
    """Schema for a single row in maintenance_logs.csv."""
    log_id: str
    equipment_id: str
    vibration_rms: float
    temp_delta: float
    oil_pressure: float
    run_hours_since_service: int
    is_anomalous_label: int = Field(
        ..., description="Evaluation-only label (0=normal, 1=anomalous). NEVER use as model input."
    )
