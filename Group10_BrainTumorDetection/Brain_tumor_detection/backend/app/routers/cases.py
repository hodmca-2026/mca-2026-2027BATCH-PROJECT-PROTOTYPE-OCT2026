import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from PIL import Image

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.config import settings
from app.core.image_checks import check_mri_like
from app.core.audit import log_action
from app.models.models import Case, MRIImage, Prediction, SymptomAssessment, User
from app.schemas.schemas import CaseCreate, CaseOut

router = APIRouter(prefix="/api/cases", tags=["cases"])


def _next_case_code(db: Session) -> str:
    count = db.query(Case).count()
    return f"CASE-{count + 1:04d}"


@router.post("", response_model=CaseOut, status_code=201)
def create_case(payload: CaseCreate, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    case = Case(
        case_code=_next_case_code(db),
        patient_ref_id=payload.patient_ref_id,
        created_by_id=current_user.id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    log_action(db, current_user.id, "CREATE_CASE", "Case", case.id)
    return case


@router.get("", response_model=list[CaseOut])
def list_cases(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    out = []
    for c in db.query(Case).order_by(Case.created_at.desc()).all():
        latest = max(c.predictions, key=lambda p: p.predicted_at) if c.predictions else None
        assessment = db.query(SymptomAssessment).filter(SymptomAssessment.case_id == c.id).first()
        out.append(CaseOut(
            id=c.id, case_code=c.case_code, patient_ref_id=c.patient_ref_id,
            status=c.status, created_at=c.created_at,
            latest_class=latest.predicted_class if latest else None,
            latest_confidence=latest.confidence_score if latest else None,
            latest_prediction_id=latest.id if latest else None,
            symptom_level=assessment.level if assessment else None,
        ))
    return out


@router.get("/{case_id}", response_model=CaseOut)
def get_case(case_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(404, "Case not found")
    return case


@router.post("/{case_id}/upload")
def upload_mri(case_id: str, file: UploadFile = File(...), db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(404, "Case not found")

    # --- validation: content type ---
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}. "
                                  f"Allowed: {settings.ALLOWED_IMAGE_TYPES}")

    contents = file.file.read()

    # --- validation: size ---
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_MB:
        raise HTTPException(400, f"File too large ({size_mb:.1f}MB). Max {settings.MAX_UPLOAD_MB}MB.")

    # --- validation: is it actually a readable image? (guards against
    # malicious files disguised with an image extension/content-type) ---
    dest_dir = settings.UPLOAD_DIR / case_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    ext = ".png" if file.content_type == "image/png" else ".jpg"
    file_id = str(uuid.uuid4())
    dest_path = dest_dir / f"{file_id}{ext}"

    with open(dest_path, "wb") as f:
        f.write(contents)

    try:
        with Image.open(dest_path) as img:
            img.verify()
    except Exception:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(400, "File is not a valid image (failed integrity check).")

    problem = check_mri_like(dest_path)
    if problem:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(400, problem)

    mri_image = MRIImage(
        case_id=case_id,
        file_path=str(dest_path),
        original_filename=file.filename,
        content_type=file.content_type,
        size_bytes=len(contents),
    )
    db.add(mri_image)
    db.commit()
    db.refresh(mri_image)
    log_action(db, current_user.id, "UPLOAD_MRI", "MRIImage", mri_image.id,
               details=f"case={case.case_code}")

    return {"image_id": mri_image.id, "message": "Uploaded successfully"}


@router.get("/{case_id}/predictions")
def case_predictions(case_id: str, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(404, "Case not found")
    preds = sorted(case.predictions, key=lambda p: p.predicted_at, reverse=True)
    return [{
        "id": p.id, "predicted_class": p.predicted_class,
        "confidence_score": p.confidence_score, "predicted_at": p.predicted_at,
        "model_version": p.model_version.version_tag,
    } for p in preds]
