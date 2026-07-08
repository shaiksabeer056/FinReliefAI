from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user") # "user" or "admin"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    financial_profile = relationship("FinancialProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    loans = relationship("Loan", back_populates="user", cascade="all, delete-orphan")
    ai_histories = relationship("AIHistory", back_populates="user", cascade="all, delete-orphan")
    settlement_predictions = relationship("SettlementPrediction", back_populates="user", cascade="all, delete-orphan")
    negotiation_letters = relationship("NegotiationLetter", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class FinancialProfile(Base):
    __tablename__ = "financial_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    phone = Column(String(50), nullable=True)
    occupation = Column(String(100), nullable=True)
    monthly_income = Column(Float, default=0.0, nullable=False)
    monthly_expenses = Column(Float, default=0.0, nullable=False)
    lump_sum_available = Column(Float, default=0.0, nullable=False)
    savings = Column(Float, default=0.0, nullable=False)
    financial_goals = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="financial_profile")


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    loan_name = Column(String(255), nullable=False)
    bank = Column(String(255), nullable=False)
    loan_type = Column(String(100), nullable=False)
    interest_rate = Column(Float, default=0.0, nullable=False)
    outstanding_amount = Column(Float, default=0.0, nullable=False)
    monthly_emi = Column(Float, default=0.0, nullable=False)
    overdue_months = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="Active") # "Active", "Settled", "Negotiating"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="loans")
    settlement_predictions = relationship("SettlementPrediction", back_populates="loan", cascade="all, delete-orphan")
    negotiation_letters = relationship("NegotiationLetter", back_populates="loan", cascade="all, delete-orphan")


class SettlementPrediction(Base):
    __tablename__ = "settlement_predictions"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    suggested_settlement_pct = Column(Float, nullable=False)
    predicted_amount = Column(Float, nullable=False)
    repayment_recommendation = Column(Text, nullable=True)
    priority_level = Column(String(50), nullable=False) # "High", "Medium", "Low"
    risk_analysis = Column(Text, nullable=True)
    negotiation_tips = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    loan = relationship("Loan", back_populates="settlement_predictions")
    user = relationship("User", back_populates="settlement_predictions")


class AIHistory(Base):
    __tablename__ = "ai_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    query_type = Column(String(100), nullable=False) # "advisor", "strategy", "letter", "general"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="ai_histories")


class NegotiationLetter(Base):
    __tablename__ = "negotiation_letters"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    borrower_info = Column(Text, nullable=True)
    loan_details = Column(Text, nullable=True)
    financial_hardship = Column(Text, nullable=True)
    settlement_request = Column(Text, nullable=True)
    repayment_proposal = Column(Text, nullable=True)
    letter_content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    loan = relationship("Loan", back_populates="negotiation_letters")
    user = relationship("User", back_populates="negotiation_letters")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    advice_type = Column(String(100), nullable=False) # "Budgeting", "Debt Reduction", "Savings", "EMI Optimization", "Investment", "Emergency Fund"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="recommendations")


class BorrowerGuide(Base):
    __tablename__ = "borrower_guides"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False) # "RBI Guidelines", "Debt Collection Rules", "Borrower Rights", "Consumer Protection", "Complaint Process", "Legal Help", "FAQs"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(100), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="audit_logs")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="notifications")
