from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import User, Loan, FinancialProfile, AuditLog, Recommendation
from app.schemas import schemas
from app.auth.auth_handler import get_current_user
from app.services import settlement_engine
from typing import List, Dict, Any

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/metrics")
def get_dashboard_metrics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).first()
    loans = db.query(Loan).filter(Loan.user_id == current_user.id).all()
    
    health = settlement_engine.calculate_financial_health(current_user, profile, loans)
    
    # Calculate priorities and risk parameters per loan
    loan_details = []
    for loan in loans:
        pred = settlement_engine.predict_settlement_parameters(loan, health)
        loan_details.append({
            "id": loan.id,
            "loan_name": loan.loan_name,
            "bank": loan.bank,
            "loan_type": loan.loan_type,
            "outstanding_amount": loan.outstanding_amount,
            "monthly_emi": loan.monthly_emi,
            "overdue_months": loan.overdue_months,
            "status": loan.status,
            "priority": pred["priority_level"],
            "risk": pred["risk_category"]
        })
        
    # Get recent audit logs for activity list
    activities = db.query(AuditLog)\
        .filter(AuditLog.user_id == current_user.id)\
        .order_by(AuditLog.timestamp.desc())\
        .limit(5)\
        .all()
        
    activities_json = [{
        "id": log.id,
        "action": log.action,
        "details": log.details,
        "timestamp": log.timestamp
    } for log in activities]

    # Get cached recommendation guides or provide default AI suggestions
    cached_recs = db.query(Recommendation)\
        .filter(Recommendation.user_id == current_user.id)\
        .order_by(Recommendation.created_at.desc())\
        .limit(3)\
        .all()
        
    suggestions = [r.content for r in cached_recs]
    if not suggestions:
        # Default AI suggestions based on stress level
        if health["debt_stress_score"] > 70:
            suggestions = [
                "High Debt Stress: Settle credit cards immediately using your lump sum.",
                "Avoid borrowing new funds. Cut down on non-essential expenses.",
                "Review RBI Fair Practice Code guidelines in the Portal to stop recovery harassment."
            ]
        elif health["debt_stress_score"] > 40:
            suggestions = [
                "Consider partial pre-payments on your highest-interest loans.",
                "Increase monthly surplus by auditing subscriptions and utility bills.",
                "Begin organizing documentation for potential One-Time Settlements (OTS)."
            ]
        else:
            suggestions = [
                "Your debt is manageable. Continue paying your EMIs on time.",
                "Begin building an emergency savings buffer (aim for 3-6 months expenses).",
                "Investigate minor pre-payments to save on interest over time."
            ]
            
    return {
        "summary": {
            "total_debt": health["total_outstanding"],
            "total_emi": health["total_emi"],
            "monthly_surplus": health["monthly_surplus"],
            "debt_stress_score": health["debt_stress_score"],
            "financial_stability_score": health["financial_stability_score"],
            "risk_category": health["risk_category"],
            "emi_ratio": health["emi_ratio"],
            "dti_ratio": health["dti_ratio"],
            "income": health["income"],
            "expenses": health["expenses"],
            "savings": health["savings"],
            "lump_sum": health["lump_sum"]
        },
        "loans": loan_details,
        "recent_activity": activities_json,
        "ai_suggestions": suggestions
    }
