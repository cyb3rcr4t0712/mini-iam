from sqlalchemy.orm import Session
from datetime import datetime
from . import models


def log_action(
    db: Session,
    user_id: int,
    action: str,
    details: str = None,
    ip_address: str = None
):
    log = models.AuditLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address,
        timestamp=datetime.utcnow()
    )
    db.add(log)
    db.commit()