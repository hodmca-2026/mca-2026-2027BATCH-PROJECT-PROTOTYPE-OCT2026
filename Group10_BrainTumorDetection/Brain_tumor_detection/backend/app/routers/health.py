from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import Case, Prediction, Report, User
from app.ml.inference import get_model_status

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/dashboard")
def dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_cases = db.query(Case).count()
    total_predictions = db.query(Prediction).count()
    pending_reviews = db.query(Report).filter(Report.review_status == "pending_review").count()
    recent_predictions = (
        db.query(Prediction).order_by(Prediction.predicted_at.desc()).limit(5).all()
    )
    model_status = get_model_status()

    return {
        "total_cases": total_cases,
        "total_predictions": total_predictions,
        "pending_reviews": pending_reviews,
        "model_status": {
            "is_placeholder": model_status["is_placeholder"],
            "architecture": model_status["architecture"],
        },
        "recent_predictions": [
            {
                "id": p.id,
                "case_code": p.case.case_code,
                "predicted_class": p.predicted_class,
                "confidence_score": p.confidence_score,
                "predicted_at": p.predicted_at,
            }
            for p in recent_predictions
        ],
        "system_status": "operational",
    }
