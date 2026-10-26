from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.guidance import build_guidance, doctor_dict
from app.models.models import Doctor, Prediction, User

router = APIRouter(prefix="/api/doctors", tags=["doctors"])


@router.get("")
def list_doctors(city: Optional[str] = None, specialization: Optional[str] = None,
                 db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Doctor)
    if city:
        q = q.filter(Doctor.city == city)
    if specialization:
        q = q.filter(Doctor.specialization == specialization)
    return [doctor_dict(d) for d in q.order_by(Doctor.city, Doctor.full_name).all()]


@router.get("/suggest/{prediction_id}")
def suggest(prediction_id: str, db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user)):
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(404, "Prediction not found")
    return build_guidance(db, prediction)
