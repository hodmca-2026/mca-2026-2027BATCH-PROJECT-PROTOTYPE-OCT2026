from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.models import ModelVersion, AuditLog, User
from app.ml.inference import get_model_status

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
def list_model_versions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    versions = db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).all()
    return [
        {
            "id": v.id,
            "version_tag": v.version_tag,
            "architecture": v.architecture,
            "dataset_info": v.dataset_info,
            "accuracy": v.accuracy,
            "precision_macro": v.precision_macro,
            "recall_macro": v.recall_macro,
            "f1_macro": v.f1_macro,
            "is_placeholder": v.is_placeholder,
            "deployment_status": v.deployment_status,
            "created_at": v.created_at,
        }
        for v in versions
    ]


@router.get("/current")
def current_model_status(current_user: User = Depends(get_current_user)):
    return get_model_status()


@router.get("/audit-logs")
def audit_logs(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()
    return [
        {
            "id": l.id, "user_id": l.user_id, "action": l.action,
            "entity_type": l.entity_type, "entity_id": l.entity_id,
            "details": l.details, "created_at": l.created_at,
        }
        for l in logs
    ]
