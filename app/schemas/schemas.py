from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# Token Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class RefreshTokenInput(BaseModel):
    refresh_token: str

# User Schemas
class UserBase(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    role: Optional[str] = "user"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Financial Profile Schemas
class FinancialProfileBase(BaseModel):
    phone: Optional[str] = None
    occupation: Optional[str] = None
    monthly_income: float = 0.0
    monthly_expenses: float = 0.0
    lump_sum_available: float = 0.0
    savings: float = 0.0
    financial_goals: Optional[str] = None

class FinancialProfileUpdate(FinancialProfileBase):
    pass

class FinancialProfileResponse(FinancialProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Loan Schemas
class LoanBase(BaseModel):
    loan_name: str
    bank: str
    loan_type: str
    interest_rate: float = Field(..., ge=0)
    outstanding_amount: float = Field(..., ge=0)
    monthly_emi: float = Field(..., ge=0)
    overdue_months: int = Field(..., ge=0)
    status: Optional[str] = "Active"

class LoanCreate(LoanBase):
    pass

class LoanUpdate(BaseModel):
    loan_name: Optional[str] = None
    bank: Optional[str] = None
    loan_type: Optional[str] = None
    interest_rate: Optional[float] = None
    outstanding_amount: Optional[float] = None
    monthly_emi: Optional[float] = None
    overdue_months: Optional[int] = None
    status: Optional[str] = None

class LoanResponse(LoanBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Settlement Prediction Schemas
class SettlementPredictionBase(BaseModel):
    loan_id: int
    suggested_settlement_pct: float
    predicted_amount: float
    repayment_recommendation: Optional[str] = None
    priority_level: str
    risk_analysis: Optional[str] = None
    negotiation_tips: Optional[str] = None

class SettlementPredictionResponse(SettlementPredictionBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# AI History Schemas
class AIHistoryBase(BaseModel):
    prompt: str
    response: str
    query_type: str

class AIHistoryCreate(AIHistoryBase):
    pass

class AIHistoryResponse(AIHistoryBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Negotiation Letter Schemas
class NegotiationLetterBase(BaseModel):
    loan_id: int
    borrower_info: Optional[str] = None
    loan_details: Optional[str] = None
    financial_hardship: Optional[str] = None
    settlement_request: Optional[str] = None
    repayment_proposal: Optional[str] = None
    letter_content: str

class NegotiationLetterResponse(NegotiationLetterBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Recommendation Schemas
class RecommendationBase(BaseModel):
    advice_type: str
    content: str

class RecommendationResponse(RecommendationBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Borrower Guide Schemas
class BorrowerGuideBase(BaseModel):
    title: str
    category: str
    content: str

class BorrowerGuideCreate(BorrowerGuideBase):
    pass

class BorrowerGuideResponse(BorrowerGuideBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Audit Log Schemas
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

# Notification Schemas
class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
