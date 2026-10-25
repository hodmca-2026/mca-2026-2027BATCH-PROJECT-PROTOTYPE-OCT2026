import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.audit import log_action
from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.ml.inference import DISCLAIMER_TEXT, get_model_status, predict_with_explanation
from app.models.models import MRIImage, ModelVersion, Prediction, User
from app.schemas.schemas import PredictionOut

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


class PredictRequest(BaseModel):
    image_id: str


def _file_url(path):
    """Turns a stored absolute path into /api/files/<relative path> (works on Windows too)."""
    if not path:
        return None
    try:
        rel = Path(path).resolve().relative_to(settings.UPLOAD_DIR.resolve())
    except ValueError:
        return None
    return "/api/files/" + rel.as_posix()


def _get_or_create_model_version(db: Session) -> ModelVersion:
    info = get_model_status()
    tag = f"{info['architecture']}-{'placeholder' if info['is_placeholder'] else 'trained'}"
    mv = db.query(ModelVersion).filter(ModelVersion.version_tag == tag).first()
    if mv:
        return mv
    test_metrics = (info.get("metrics") or {}).get("test_metrics", {})
    mv = ModelVersion(
        version_tag=tag, architecture=info["architecture"],
        dataset_info="Kaggle Brain Tumor MRI Dataset (Nickparvar) - glioma/meningioma/pituitary/notumor",
        accuracy=test_metrics.get("accuracy"), precision_macro=test_metrics.get("precision_macro"),
        recall_macro=test_metrics.get("recall_macro"), f1_macro=test_metrics.get("f1_macro"),
        is_placeholder=info["is_placeholder"], deployment_status="active",
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)
    return mv


def _to_prediction_out(p: Prediction) -> PredictionOut:
    return PredictionOut(
        id=p.id, case_id=p.case_id, predicted_class=p.predicted_class,
        confidence_score=p.confidence_score,
        all_class_probabilities=json.loads(p.all_class_probabilities),
        original_url=_file_url(p.image.file_path),
        heatmap_url=_file_url(p.heatmap_path), overlay_url=_file_url(p.overlay_path),
        disclaimer=DISCLAIMER_TEXT, model_version=p.model_version.version_tag,
        predicted_at=p.predicted_at,
    )


@router.post("", response_model=PredictionOut, status_code=201)
def create_prediction(payload: PredictRequest, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    image = db.query(MRIImage).filter(MRIImage.id == payload.image_id).first()
    if not image:
        raise HTTPException(404, "MRI image not found")

    model_version = _get_or_create_model_version(db)
    stem = image.file_path.rsplit(".", 1)[0]
    heatmap_path, overlay_path = stem + "_heatmap.png", stem + "_overlay.png"
    result = predict_with_explanation(image.file_path, heatmap_path, overlay_path)

    prediction = Prediction(
        case_id=image.case_id, image_id=image.id, model_version_id=model_version.id,
        predicted_class=result["predicted_class"], confidence_score=result["confidence_score"],
        all_class_probabilities=json.dumps(result["all_class_probabilities"]),
        heatmap_path=heatmap_path, overlay_path=overlay_path,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    log_action(db, current_user.id, "RUN_PREDICTION", "Prediction", prediction.id,
               details=f"placeholder_model={result['is_placeholder']}")
    return _to_prediction_out(prediction)


@router.get("/{prediction_id}", response_model=PredictionOut)
def get_prediction(prediction_id: str, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(404, "Prediction not found")
    return _to_prediction_out(prediction)


@router.get("/{prediction_id}/explanation")
def get_explanation(prediction_id: str, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    p = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not p:
        raise HTTPException(404, "Prediction not found")
    return {
        "prediction_id": p.id, "predicted_class": p.predicted_class,
        "confidence_score": p.confidence_score, "original_url": _file_url(p.image.file_path),
        "heatmap_url": _file_url(p.heatmap_path), "overlay_url": _file_url(p.overlay_path),
        "disclaimer": DISCLAIMER_TEXT,
    }
