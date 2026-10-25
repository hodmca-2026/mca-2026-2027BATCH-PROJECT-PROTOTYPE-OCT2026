import json
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.audit import log_action
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import Case, SymptomAssessment, User
from app.routers.cases import _next_case_code

router = APIRouter(prefix="/api/symptoms", tags=["symptoms"])

# Transparent, rule-based scoring. Weights are simple judgement values (NOT
# derived from patient data), so the output is a screening *indicator*, not a
# validated prediction or diagnosis. Answers: 0 = never, 1 = sometimes, 2 = often.
QUESTIONS = [
    {"id": "headache", "weight": 2},
    {"id": "headache_morning", "weight": 2},
    {"id": "nausea", "weight": 1},
    {"id": "vision", "weight": 2},
    {"id": "seizures", "weight": 3},
    {"id": "weakness", "weight": 3},
    {"id": "speech", "weight": 3},
    {"id": "memory", "weight": 2},
    {"id": "balance", "weight": 2},
    {"id": "mood", "weight": 1},
    {"id": "hearing", "weight": 1},
    {"id": "persistent", "weight": 2},
]
RED_FLAG_IDS = {"seizures", "weakness", "speech", "vision"}
VALID_IDS = {q["id"] for q in QUESTIONS}


def score_answers(answers: Dict[str, int]) -> dict:
    total, max_total, red = 0, 0, []
    for q in QUESTIONS:
        v = int(answers.get(q["id"], 0))
        total += q["weight"] * v
        max_total += q["weight"] * 2
        if q["id"] in RED_FLAG_IDS and v >= 1:
            red.append(q["id"])
    ratio = total / max_total
    level = "low" if ratio < 0.20 else "moderate" if ratio < 0.45 else "high"
    if red and level == "low":
        level = "moderate"
    return {"score": total, "max_score": max_total, "level": level, "red_flags": red}


class AssessRequest(BaseModel):
    patient_ref_id: str = Field(min_length=1, max_length=60)
    answers: Dict[str, int]


@router.get("/questions")
def questions(current_user: User = Depends(get_current_user)):
    return QUESTIONS


@router.post("/assess", status_code=201)
def assess(payload: AssessRequest, db: Session = Depends(get_db),
           current_user: User = Depends(get_current_user)):
    unknown = set(payload.answers) - VALID_IDS
    if unknown:
        raise HTTPException(400, f"Unknown question ids: {sorted(unknown)}")
    if any(v not in (0, 1, 2) for v in payload.answers.values()):
        raise HTTPException(400, "Answers must be 0, 1 or 2.")

    result = score_answers(payload.answers)
    case = Case(case_code=_next_case_code(db), patient_ref_id=payload.patient_ref_id.strip(),
                created_by_id=current_user.id)
    db.add(case)
    db.commit()
    db.refresh(case)

    db.add(SymptomAssessment(
        case_id=case.id, answers=json.dumps(payload.answers), score=result["score"],
        max_score=result["max_score"], level=result["level"], red_flags=json.dumps(result["red_flags"]),
    ))
    db.commit()
    log_action(db, current_user.id, "SYMPTOM_ASSESSMENT", "Case", case.id, details=f"level={result['level']}")
    return {"case_id": case.id, "case_code": case.case_code, **result}


@router.get("/case/{case_id}")
def get_assessment(case_id: str, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    a = db.query(SymptomAssessment).filter(SymptomAssessment.case_id == case_id).first()
    if not a:
        raise HTTPException(404, "No symptom assessment for this case")
    return {"case_id": case_id, "level": a.level, "score": a.score, "max_score": a.max_score,
            "red_flags": json.loads(a.red_flags or "[]"), "answers": json.loads(a.answers)}
