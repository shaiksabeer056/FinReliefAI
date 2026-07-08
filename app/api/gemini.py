from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import User, Loan, FinancialProfile, AIHistory, SettlementPrediction, NegotiationLetter, Recommendation
from app.schemas import schemas
from app.auth.auth_handler import get_current_user
from app.services import settlement_engine
from app.services.pdf_generator import generate_pdf_letter
from app.utils.audit import log_action
from io import BytesIO

router = APIRouter(prefix="/api/gemini", tags=["Gemini AI Features"])

@router.post("/predict/{loan_id}", response_model=schemas.SettlementPredictionResponse)
def get_loan_prediction(
    loan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    loan = db.query(Loan).filter(Loan.id == loan_id, Loan.user_id == current_user.id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
        
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).first()
    loans = db.query(Loan).filter(Loan.user_id == current_user.id).all()
    health = settlement_engine.calculate_financial_health(current_user, profile, loans)
    
    ai_pred = settlement_engine.get_ai_settlement_prediction(current_user, profile, loan, health)
    
    # Store in DB
    db_pred = SettlementPrediction(
        loan_id=loan.id,
        user_id=current_user.id,
        suggested_settlement_pct=ai_pred["suggested_settlement_pct"],
        predicted_amount=ai_pred["predicted_amount"],
        repayment_recommendation=ai_pred["repayment_recommendation"],
        priority_level=ai_pred["priority_level"],
        risk_analysis=ai_pred["risk_analysis"],
        negotiation_tips=ai_pred["negotiation_tips"]
    )
    db.add(db_pred)
    
    prompt = f"Predict settlement details for loan {loan.loan_name}."
    response_txt = f"Pct: {ai_pred['suggested_settlement_pct']}%, Rec: {ai_pred['repayment_recommendation']}"
    
    db_history = AIHistory(
        user_id=current_user.id,
        prompt=prompt,
        response=response_txt,
        query_type="Settlement Prediction"
    )
    db.add(db_history)
    db.commit()
    db.refresh(db_pred)
    
    log_action(db, "AI Prediction", f"Generated settlement prediction for loan: {loan.loan_name}", user_id=current_user.id)
    return db_pred

@router.post("/strategy")
def get_strategy(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).first()
    loans = db.query(Loan).filter(Loan.user_id == current_user.id).all()
    if not loans:
        raise HTTPException(status_code=400, detail="Please add at least one loan to generate an AI strategy.")
        
    health = settlement_engine.calculate_financial_health(current_user, profile, loans)
    strategy_text = settlement_engine.get_ai_negotiation_strategy(current_user, profile, loans, health)
    
    db_history = AIHistory(
        user_id=current_user.id,
        prompt=f"Generate complete strategy for user with monthly income {health['income']}.",
        response=strategy_text,
        query_type="Negotiation Strategy"
    )
    db.add(db_history)
    db.commit()
    
    log_action(db, "AI Strategy", "Generated global debt strategy", user_id=current_user.id)
    return {"strategy": strategy_text}

@router.post("/generate-letter")
def generate_proposal_letter(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    loan_id = payload.get("loan_id")
    settlement_pct = payload.get("settlement_pct")
    predicted_amount = payload.get("predicted_amount")
    
    if not loan_id:
        raise HTTPException(status_code=400, detail="loan_id is required")
        
    loan = db.query(Loan).filter(Loan.id == loan_id, Loan.user_id == current_user.id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
        
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).first()
    
    if not settlement_pct or not predicted_amount:
        # compute defaults
        loans = db.query(Loan).filter(Loan.user_id == current_user.id).all()
        health = settlement_engine.calculate_financial_health(current_user, profile, loans)
        rule_params = settlement_engine.predict_settlement_parameters(loan, health)
        settlement_pct = rule_params["suggested_settlement_pct"]
        predicted_amount = rule_params["predicted_amount"]
        
    letter_text = settlement_engine.get_ai_negotiation_letter(current_user, profile, loan, settlement_pct, predicted_amount)
    
    # Store letter
    db_letter = NegotiationLetter(
        loan_id=loan.id,
        user_id=current_user.id,
        borrower_info=current_user.name,
        loan_details=f"{loan.loan_name} - {loan.bank}",
        financial_hardship=f"Income vs expenses constraint",
        settlement_request=f"{settlement_pct}% settlement",
        repayment_proposal=f"One-time payment of Rs. {predicted_amount}",
        letter_content=letter_text
    )
    db.add(db_letter)
    
    db_history = AIHistory(
        user_id=current_user.id,
        prompt=f"Draft settlement letter for loan {loan.loan_name} at {settlement_pct}%.",
        response=letter_text,
        query_type="Negotiation Letter"
    )
    db.add(db_history)
    db.commit()
    db.refresh(db_letter)
    
    log_action(db, "AI Letter", f"Generated settlement proposal letter for loan ID: {loan.id}", user_id=current_user.id)
    
    return {
        "letter_id": db_letter.id,
        "letter_content": letter_text
    }

@router.post("/advisor")
def consult_financial_advisor(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    advice_type = payload.get("advice_type", "Budgeting")
    allowed_types = ["Budgeting", "Debt Reduction", "Savings", "EMI Optimization", "Investment", "Emergency Fund"]
    if advice_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid advice topic requested")
        
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).first()
    loans = db.query(Loan).filter(Loan.user_id == current_user.id).all()
    health = settlement_engine.calculate_financial_health(current_user, profile, loans)
    
    advice_text = settlement_engine.get_ai_financial_advice(current_user, profile, loans, health, advice_type)
    
    # Store Recommendation
    db_rec = Recommendation(
        user_id=current_user.id,
        advice_type=advice_type,
        content=advice_text
    )
    db.add(db_rec)
    
    db_history = AIHistory(
        user_id=current_user.id,
        prompt=f"Provide advice on {advice_type}",
        response=advice_text,
        query_type=f"Advisor - {advice_type}"
    )
    db.add(db_history)
    db.commit()
    
    log_action(db, "AI Advisor", f"Consulted financial advisor on: {advice_type}", user_id=current_user.id)
    return {"advice": advice_text}

@router.get("/letter/pdf/{letter_id}")
def download_letter_pdf(
    letter_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    letter_obj = db.query(NegotiationLetter).filter(NegotiationLetter.id == letter_id, NegotiationLetter.user_id == current_user.id).first()
    if not letter_obj:
        raise HTTPException(status_code=404, detail="Negotiation letter not found")
        
    pdf_data = generate_pdf_letter(letter_obj.letter_content)
    
    # Return as StreamingResponse
    return StreamingResponse(
        BytesIO(pdf_data),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=negotiation_letter_{letter_id}.pdf"}
    )
