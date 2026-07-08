from sqlalchemy.orm import Session
from app.models.models import AuditLog
from fastapi import Request

def log_action(db: Session, action: str, details: str, user_id: int = None, request: Request = None):
    ip_address = None
    if request:
        ip_address = request.client.host if request.client else "unknown"
    
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address
    )
    db.add(log_entry)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        # Suppress log error to avoid breaking request flow
        print(f"Failed to write audit log: {e}")
