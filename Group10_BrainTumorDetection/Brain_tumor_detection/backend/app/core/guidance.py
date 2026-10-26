"""
Non-clinical guidance for the result screen and the PDF report.

IMPORTANT: this module never recommends treatment or medication. It only
produces (a) generic "next step" messages (consult a specialist, bring the
original scans, treat low-confidence results with caution) and (b) a ranked
list of specialists from the doctor directory.
"""
import json
from sqlalchemy.orm import Session

from app.models.models import Doctor, Prediction, SymptomAssessment

STEP_TEXT = {
    "consult_specialist": "Share these results with a qualified neurologist or neurosurgeon for professional evaluation.",
    "bring_scan": "Bring the original MRI scans and reports (not only this summary) to your appointment.",
    "low_confidence": "The model's confidence is below 70%; treat this result as especially uncertain and ask for a second review.",
    "placeholder": "This result comes from an untrained demo model and has no clinical meaning.",
    "symptoms_urgent": "Warning-sign symptoms were reported (e.g. seizures, weakness, speech or vision changes). Seek prompt medical attention rather than waiting for a routine appointment.",
    "symptoms_high": "The symptom indicator is high; discuss the symptoms with a doctor soon.",
    "no_tumor_but_symptoms": "The model did not flag a tumor class, but a model result does not rule out other conditions. If symptoms persist, see a doctor.",
    "not_diagnosis": "This tool is for research and education and does not provide a diagnosis.",
}


def specializations_for(predicted_class: str) -> list[str]:
    if predicted_class == "pituitary":
        return ["Neurosurgeon", "Endocrinologist", "Neurologist"]
    if predicted_class in ("glioma", "meningioma"):
        return ["Neurosurgeon", "Neuro-oncologist", "Neurologist"]
    return ["Neurologist"]


def doctor_dict(d: Doctor) -> dict:
    return {
        "id": d.id, "full_name": d.full_name, "degree": d.degree,
        "specialization": d.specialization, "hospital": d.hospital,
        "city": d.city, "address": d.address, "phone": d.phone,
        "is_demo": bool(d.is_demo),
    }


def build_guidance(db: Session, prediction: Prediction) -> dict:
    a = db.query(SymptomAssessment).filter(SymptomAssessment.case_id == prediction.case_id).first()
    assessment, level, red_flags = None, None, []
    if a:
        level = a.level
        red_flags = json.loads(a.red_flags or "[]")
        assessment = {
            "level": a.level, "score": a.score, "max_score": a.max_score,
            "red_flags": red_flags, "answers": json.loads(a.answers),
        }

    keys = []
    if prediction.model_version.is_placeholder:
        keys.append("placeholder")
    if red_flags:
        keys.append("symptoms_urgent")
    if level == "high":
        keys.append("symptoms_high")
    if prediction.confidence_score < 0.70:
        keys.append("low_confidence")
    if prediction.predicted_class == "notumor" and level in ("moderate", "high"):
        keys.append("no_tumor_but_symptoms")
    keys += ["consult_specialist", "bring_scan", "not_diagnosis"]

    specs = specializations_for(prediction.predicted_class)
    all_docs = db.query(Doctor).all()

    def rank(d):
        return specs.index(d.specialization) if d.specialization in specs else len(specs)

    ordered = sorted(all_docs, key=lambda d: (rank(d), d.city, d.full_name))
    matched = [d for d in ordered if d.specialization in specs][:4] or ordered[:4]

    return {
        "assessment": assessment,
        "next_steps": [{"key": k, "text": STEP_TEXT[k]} for k in keys],
        "specializations": specs,
        "doctors": [doctor_dict(d) for d in matched],
    }
