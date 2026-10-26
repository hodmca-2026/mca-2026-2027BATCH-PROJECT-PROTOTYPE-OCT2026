from sqlalchemy.orm import Session
from app.models.models import AuditLog


def log_action(db: Session, user_id: str | None, action: str,
                entity_type: str | None = None, entity_id: str | None = None,
                details: str | None = None):
    entry = AuditLog(
        user_id=user_id, action=action,
        entity_type=entity_type, entity_id=entity_id, details=details,
    )
    db.add(entry)
    db.commit()
