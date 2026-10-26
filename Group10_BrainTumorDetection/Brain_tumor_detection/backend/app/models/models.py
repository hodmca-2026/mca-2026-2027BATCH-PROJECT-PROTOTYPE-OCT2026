"""
Database schema.

Tables: Role, User, Case (patient/case reference), MRIImage, ModelVersion,
Prediction, Report, AuditLog.

Written in plain SQLAlchemy so it runs unchanged against SQLite (dev
default) or SQL Server (set DATABASE_URL -- see app/core/config.py).
No patient-identifying data is stored beyond an opaque `patient_ref_id`
the doctor/researcher supplies -- per the "no unnecessary personal
medical information" requirement.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Text, Enum, Boolean
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class RoleEnum(str, enum.Enum):
    doctor = "doctor"
    researcher = "researcher"
    admin = "admin"


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(Enum(RoleEnum), unique=True, nullable=False)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    role = relationship("Role", back_populates="users")
    cases = relationship("Case", back_populates="created_by")


class Case(Base):
    """A case = one patient reference + its MRI/prediction/report history."""
    __tablename__ = "cases"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    case_code = Column(String(30), unique=True, nullable=False)  # e.g. CASE-0001
    patient_ref_id = Column(String(60), nullable=False)          # opaque ref, not PII
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(String(30), default="open")  # open / reviewed / closed
    created_at = Column(DateTime, default=datetime.utcnow)

    created_by = relationship("User", back_populates="cases")
    images = relationship("MRIImage", back_populates="case", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="case", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="case", cascade="all, delete-orphan")


class MRIImage(Base):
    __tablename__ = "mri_images"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(60), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="images")
    predictions = relationship("Prediction", back_populates="image")


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    version_tag = Column(String(50), unique=True, nullable=False)  # e.g. v1.0-resnet18
    architecture = Column(String(50))
    dataset_info = Column(Text)
    accuracy = Column(Float, nullable=True)
    precision_macro = Column(Float, nullable=True)
    recall_macro = Column(Float, nullable=True)
    f1_macro = Column(Float, nullable=True)
    is_placeholder = Column(Boolean, default=True)
    deployment_status = Column(String(30), default="inactive")  # active / inactive
    created_at = Column(DateTime, default=datetime.utcnow)

    predictions = relationship("Prediction", back_populates="model_version")


class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False)
    image_id = Column(String(36), ForeignKey("mri_images.id"), nullable=False)
    model_version_id = Column(String(36), ForeignKey("model_versions.id"), nullable=False)

    predicted_class = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)
    all_class_probabilities = Column(Text)  # JSON string {class: prob}
    heatmap_path = Column(String(500))
    overlay_path = Column(String(500))
    predicted_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="predictions")
    image = relationship("MRIImage", back_populates="predictions")
    model_version = relationship("ModelVersion", back_populates="predictions")
    report = relationship("Report", back_populates="prediction", uselist=False)


class Report(Base):
    __tablename__ = "reports"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False)
    prediction_id = Column(String(36), ForeignKey("predictions.id"), unique=True, nullable=False)

    draft_content = Column(Text, nullable=False)       # AI-generated draft
    reviewed_content = Column(Text, nullable=True)      # doctor-edited version
    is_ai_generated = Column(Boolean, default=True)
    review_status = Column(String(30), default="pending_review")  # pending_review / approved
    reviewed_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    case = relationship("Case", back_populates="reports")
    prediction = relationship("Prediction", back_populates="report")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    action = Column(String(120), nullable=False)   # e.g. "LOGIN", "UPLOAD_MRI", "GENERATE_REPORT"
    entity_type = Column(String(60), nullable=True)
    entity_id = Column(String(36), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Doctor(Base):
    """Specialist directory. Seeded with clearly-labelled DEMO entries."""
    __tablename__ = "doctors"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    full_name = Column(String(120), nullable=False)
    degree = Column(String(200), nullable=False)
    specialization = Column(String(80), nullable=False)
    hospital = Column(String(160), nullable=True)
    city = Column(String(80), nullable=False)
    address = Column(String(255), nullable=True)
    phone = Column(String(40), nullable=False)
    is_demo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SymptomAssessment(Base):
    """Rule-based symptom questionnaire result, one per case."""
    __tablename__ = "symptom_assessments"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    case_id = Column(String(36), ForeignKey("cases.id"), unique=True, nullable=False)
    answers = Column(Text, nullable=False)       # JSON {question_id: 0|1|2}
    score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    level = Column(String(20), nullable=False)   # low | moderate | high
    red_flags = Column(Text, nullable=True)      # JSON list of question ids
    created_at = Column(DateTime, default=datetime.utcnow)
