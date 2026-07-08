from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.models.models import BorrowerGuide
from app.schemas import schemas
from app.auth.auth_handler import get_current_user
from app.models.models import User

router = APIRouter(prefix="/api/guides", tags=["Borrower Rights Guides"])

# Pre-populated static guides in case DB is empty
DEFAULT_GUIDES = [
    {
        "title": "RBI Fair Practice Code Guidelines",
        "category": "RBI Guidelines",
        "content": "The Reserve Bank of India (RBI) mandates that lenders must behave transparently. Key rules:\n1. All terms, interest rates, processing charges, and penal rates must be disclosed in writing.\n2. Lenders cannot change loan terms unilaterally without proper notice.\n3. Borrowers must receive a complete Loan Agreement copy upon disbursal."
    },
    {
        "title": "Debt Collection Rules & Harassment Protection",
        "category": "Debt Collection Rules",
        "content": "Lenders and recovery agents are bound by legal limits:\n1. Agents can only call or visit between 8:00 AM and 7:00 PM.\n2. Verbal abuse, physical intimidation, or public shaming is strictly illegal under RBI circulars.\n3. Agents must carry authorization letters and proper ID when visiting."
    },
    {
        "title": "Core Borrower Rights in India",
        "category": "Borrower Rights",
        "content": "As a borrower, you retain constitutional and legal protections:\n1. **Right to Privacy**: Lenders cannot disclose your debt details to friends, neighbors, or colleagues.\n2. **Right to be Heard**: Lenders must provide a grievance mechanism.\n3. **Right to Settlement**: You can legally negotiate an Outstanding Settlement."
    },
    {
        "title": "RBI Ombudsman Complaint Process",
        "category": "Complaint Process",
        "content": "If a bank or NBFC violates collection guidelines or ignores complaints:\n1. File a written complaint to the bank's Grievance Redressal Officer (GRO).\n2. If unresolved within 30 days, file an online appeal to the RBI Ombudsman via the CMS portal (https://cms.rbi.org.in).\n3. RBI Ombudsman decisions are binding on the bank."
    },
    {
        "title": "Frequently Asked Questions (FAQs)",
        "category": "FAQs",
        "content": "Q: Does One-Time Settlement (OTS) ruin my credit score?\nA: Settle reduces your credit score because the account status is updated to 'Settled' rather than 'Closed'. However, it removes the outstanding liability, allowing you to rebuild credit over time.\n\nQ: Can recovery agents enter my house without permission?\nA: No, recovery agents have no legal authority to enter your property without consent. You can contact police if they trespass."
    }
]

@router.get("", response_model=List[schemas.BorrowerGuideResponse])
def list_guides(current_user: User = Depends(get_current_user) if True else None, db: Session = Depends(get_db)):
    guides = db.query(BorrowerGuide).all()
    
    # Pre-populate on-the-fly if table is empty
    if not guides:
        for g in DEFAULT_GUIDES:
            db_guide = BorrowerGuide(
                title=g["title"],
                category=g["category"],
                content=g["content"]
            )
            db.add(db_guide)
        db.commit()
        guides = db.query(BorrowerGuide).all()
        
    return guides
