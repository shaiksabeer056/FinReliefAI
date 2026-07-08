from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.models.models import Loan, User
from app.schemas import schemas
from app.auth.auth_handler import get_current_user
from app.utils.audit import log_action

router = APIRouter(prefix="/api/loans", tags=["Loan Management"])

@router.get("", response_model=List[schemas.LoanResponse])
def list_loans(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Loan).filter(Loan.user_id == current_user.id).all()

@router.post("", response_model=schemas.LoanResponse, status_code=status.HTTP_201_CREATED)
def create_loan(
    loan_data: schemas.LoanCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_loan = Loan(
        user_id=current_user.id,
        loan_name=loan_data.loan_name,
        bank=loan_data.bank,
        loan_type=loan_data.loan_type,
        interest_rate=loan_data.interest_rate,
        outstanding_amount=loan_data.outstanding_amount,
        monthly_emi=loan_data.monthly_emi,
        overdue_months=loan_data.overdue_months,
        status=loan_data.status or "Active"
    )
    db.add(new_loan)
    db.commit()
    db.refresh(new_loan)
    
    log_action(
        db, 
        "Create Loan", 
        f"Loan added: {new_loan.loan_name} from {new_loan.bank} - Rs. {new_loan.outstanding_amount}", 
        user_id=current_user.id, 
        request=request
    )
    return new_loan

@router.get("/{loan_id}", response_model=schemas.LoanResponse)
def get_loan(
    loan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    loan = db.query(Loan).filter(Loan.id == loan_id, Loan.user_id == current_user.id).first()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    return loan

@router.put("/{loan_id}", response_model=schemas.LoanResponse)
def update_loan(
    loan_id: int,
    loan_data: schemas.LoanUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    loan = db.query(Loan).filter(Loan.id == loan_id, Loan.user_id == current_user.id).first()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
        
    for key, value in loan_data.model_dump(exclude_unset=True).items():
        setattr(loan, key, value)
        
    db.commit()
    db.refresh(loan)
    
    log_action(db, "Update Loan", f"Loan updated: {loan.loan_name} (ID: {loan.id})", user_id=current_user.id, request=request)
    return loan

@router.delete("/{loan_id}")
def delete_loan(
    loan_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    loan = db.query(Loan).filter(Loan.id == loan_id, Loan.user_id == current_user.id).first()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
        
    loan_name = loan.loan_name
    db.delete(loan)
    db.commit()
    
    log_action(db, "Delete Loan", f"Loan deleted: {loan_name} (ID: {loan_id})", user_id=current_user.id, request=request)
    return {"message": f"Loan '{loan_name}' deleted successfully"}
