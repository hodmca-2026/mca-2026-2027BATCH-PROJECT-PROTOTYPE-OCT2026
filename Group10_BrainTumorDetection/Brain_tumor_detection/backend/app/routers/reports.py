import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.audit import log_action
from app.models.models import Prediction, Report, User
from app.schemas.schemas import ReportGenerateRequest, ReportOut, ReportReviewRequest
from app.genai.report_generator import generate_draft_report
from app.core.guidance import build_guidance
from app.core.pdf_report import build_report_pdf

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/generate", response_model=ReportOut, status_code=201)
def generate_report(payload: ReportGenerateRequest, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    prediction = db.query(Prediction).filter(Prediction.id == payload.prediction_id).first()
    if not prediction:
        raise HTTPException(404, "Prediction not found")

    existing = db.query(Report).filter(Report.prediction_id == prediction.id).first()
    if existing:
        return existing

    from app.ml.inference import DISCLAIMER_TEXT
    data = {
        "case_code": prediction.case.case_code,
        "patient_ref_id": prediction.case.patient_ref_id,
        "model_version": prediction.model_version.version_tag,
        "predicted_class": prediction.predicted_class,
        "confidence_score": prediction.confidence_score,
        "all_class_probabilities": json.loads(prediction.all_class_probabilities),
        "disclaimer": DISCLAIMER_TEXT,
        "is_placeholder": prediction.model_version.is_placeholder,
    }
    draft = generate_draft_report(data)

    report = Report(
        case_id=prediction.case_id,
        prediction_id=prediction.id,
        draft_content=draft,
        is_ai_generated=True,
        review_status="pending_review",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    log_action(db, current_user.id, "GENERATE_REPORT", "Report", report.id)
    return report


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")
    return report


@router.put("/{report_id}/review", response_model=ReportOut)
def review_report(report_id: str, payload: ReportReviewRequest, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")

    report.reviewed_content = payload.reviewed_content
    report.reviewed_by_id = current_user.id
    report.reviewed_at = datetime.utcnow()
    report.review_status = "approved" if payload.approve else "pending_review"
    db.commit()
    db.refresh(report)
    log_action(db, current_user.id, "REVIEW_REPORT", "Report", report.id,
               details=f"approved={payload.approve}")
    return report


@router.get("/{report_id}/download")
def download_report(report_id: str, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")
    prediction = report.prediction
    case = report.case
    guidance = build_guidance(db, prediction)
    pdf_bytes = build_report_pdf(
        case_code=case.case_code,
        patient_ref=case.patient_ref_id,
        predicted_class=prediction.predicted_class,
        confidence=prediction.confidence_score,
        probabilities=json.loads(prediction.all_class_probabilities),
        model_version=prediction.model_version.version_tag,
        is_placeholder=bool(prediction.model_version.is_placeholder),
        report_text=report.reviewed_content or report.draft_content,
        review_status=report.review_status,
        assessment=guidance["assessment"],
        next_steps=guidance["next_steps"],
        doctors=guidance["doctors"],
        overlay_path=prediction.overlay_path,
        original_path=prediction.image.file_path,
    )
    log_action(db, current_user.id, "DOWNLOAD_REPORT", "Report", report.id)
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{case.case_code}-report.pdf"'},
    )
