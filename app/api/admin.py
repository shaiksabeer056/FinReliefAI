from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from app.database.connection import get_db
from app.models.models import User, Loan, AIHistory, AuditLog, FinancialProfile
from app.schemas import schemas
from app.auth.auth_handler import get_current_admin
from app.utils.audit import log_action

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"], dependencies=[Depends(get_current_admin)])

@router.get("/users", response_model=List[schemas.UserResponse])
def admin_list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.put("/users/{user_id}/role")
def admin_update_user_role(user_id: int, payload: dict, db: Session = Depends(get_db)):
    new_role = payload.get("role")
    if new_role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role specified")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.role = new_role
    db.commit()
    return {"message": f"User {user.email} role updated to {new_role}"}

@router.delete("/users/{user_id}")
def admin_delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db.delete(user)
    db.commit()
    return {"message": f"User {user.email} deleted successfully"}

@router.get("/loans")
def admin_list_loans(db: Session = Depends(get_db)):
    loans = db.query(Loan).all()
    response = []
    for l in loans:
        user_email = db.query(User.email).filter(User.id == l.user_id).scalar()
        response.append({
            "id": l.id,
            "user_id": l.user_id,
            "user_email": user_email or "unknown",
            "loan_name": l.loan_name,
            "bank": l.bank,
            "loan_type": l.loan_type,
            "interest_rate": l.interest_rate,
            "outstanding_amount": l.outstanding_amount,
            "monthly_emi": l.monthly_emi,
            "overdue_months": l.overdue_months,
            "status": l.status,
            "created_at": l.created_at
        })
    return response

@router.get("/metrics")
def admin_get_metrics(db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_loans = db.query(Loan).count()
    total_debt = db.query(func.sum(Loan.outstanding_amount)).scalar() or 0.0
    total_ai_calls = db.query(AIHistory).count()
    
    # AI Query Type distribution
    ai_distribution_raw = db.query(AIHistory.query_type, func.count(AIHistory.id))\
        .group_by(AIHistory.query_type)\
        .all()
    ai_distribution = {q_type: count for q_type, count in ai_distribution_raw}
    
    # Audit log user activities summary (last 20 logs)
    recent_activities = db.query(AuditLog)\
        .order_by(AuditLog.timestamp.desc())\
        .limit(20)\
        .all()
        
    activities = [{
        "id": log.id,
        "user_id": log.user_id,
        "action": log.action,
        "details": log.details,
        "ip_address": log.ip_address,
        "timestamp": log.timestamp
    } for log in recent_activities]
    
    return {
        "metrics": {
            "total_users": total_users,
            "total_loans": total_loans,
            "total_debt": total_debt,
            "total_ai_calls": total_ai_calls
        },
        "ai_distribution": ai_distribution,
        "recent_activities": activities
    }
