import json
from typing import List, Dict, Any, Optional
from app.models.models import User, Loan, FinancialProfile
from app.ai.gemini_service import call_gemini

def calculate_financial_health(user: User, profile: Optional[FinancialProfile], loans: List[Loan]) -> Dict[str, Any]:
    """Calculate core borrower financial health metrics."""
    income = profile.monthly_income if profile else 0.0
    expenses = profile.monthly_expenses if profile else 0.0
    lump_sum = profile.lump_sum_available if profile else 0.0
    savings = profile.savings if profile else 0.0
    
    total_outstanding = sum(loan.outstanding_amount for loan in loans)
    total_emi = sum(loan.monthly_emi for loan in loans)
    
    monthly_surplus = income - expenses
    
    dti_ratio = 0.0
    emi_ratio = 0.0
    if income > 0:
        dti_ratio = round((total_emi + expenses) / income, 4)
        emi_ratio = round(total_emi / income, 4)
        
    # Stress Score formulation: combination of DTI and overdue loans
    max_overdue_months = max([loan.overdue_months for loan in loans], default=0)
    stress_score_raw = (dti_ratio * 70) + (min(max_overdue_months, 12) / 12 * 30)
    debt_stress_score = max(0.0, min(100.0, round(stress_score_raw, 2)))
    
    # Financial Stability Score formulation: income-surplus buffer + savings buffer
    savings_to_debt_ratio = savings / total_outstanding if total_outstanding > 0 else 1.0
    stability_raw = 100.0 - debt_stress_score + (min(savings_to_debt_ratio, 1.0) * 20.0)
    financial_stability_score = max(0.0, min(100.0, round(stability_raw, 2)))
    
    if debt_stress_score > 75:
        risk_category = "High Risk"
    elif debt_stress_score > 40:
        risk_category = "Medium Risk"
    else:
        risk_category = "Low Risk"
        
    return {
        "income": income,
        "expenses": expenses,
        "lump_sum": lump_sum,
        "savings": savings,
        "total_outstanding": total_outstanding,
        "total_emi": total_emi,
        "monthly_surplus": monthly_surplus,
        "emi_ratio": round(emi_ratio * 100, 2), # percentage
        "dti_ratio": round(dti_ratio * 100, 2), # percentage
        "debt_stress_score": debt_stress_score,
        "financial_stability_score": financial_stability_score,
        "risk_category": risk_category
    }

def predict_settlement_parameters(loan: Loan, health_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate rule-based parameters for settlement. Used for fallbacks and input feeds."""
    overdue = loan.overdue_months
    outstanding = loan.outstanding_amount
    loan_type = loan.loan_type.lower()
    
    # Base settlement percentage is high if early overdue, decreases over time
    # e.g., credit card can go down to 40%, secured loan only down to 70%
    if "credit card" in loan_type or "personal" in loan_type or "unsecured" in loan_type:
        base_pct = 70.0
        # drop 5% per month overdue
        settlement_pct = max(35.0, base_pct - (overdue * 5.0))
        risk = "High" if overdue >= 6 else "Medium" if overdue >= 3 else "Low"
    else: # secured loan
        base_pct = 90.0
        # drop 2% per month overdue
        settlement_pct = max(70.0, base_pct - (overdue * 2.0))
        risk = "Medium" if overdue >= 6 else "Low"
        
    predicted_amount = round(outstanding * (settlement_pct / 100.0), 2)
    
    # Priority
    if overdue >= 6 or outstanding > 200000:
        priority = "High"
    elif overdue >= 3 or outstanding > 50000:
        priority = "Medium"
    else:
        priority = "Low"
        
    return {
        "suggested_settlement_pct": settlement_pct,
        "predicted_amount": predicted_amount,
        "priority_level": priority,
        "risk_category": risk
    }

def get_ai_settlement_prediction(user: User, profile: Optional[FinancialProfile], loan: Loan, health_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Predict settlement rate and return detailed tips using Gemini or rule-based fallback."""
    rule_results = predict_settlement_parameters(loan, health_metrics)
    
    prompt = f"""
    You are an AI Settlement Predictor specializing in bank negotiations.
    Predict the settlement conditions for this loan.
    
    BORROWER DETAILS:
    - Monthly Income: Rs. {health_metrics['income']:.2f}
    - Total Expenses: Rs. {health_metrics['expenses']:.2f}
    - Lump Sum Available: Rs. {health_metrics['lump_sum']:.2f}
    
    LOAN DETAILS:
    - Bank/Lender: {loan.bank}
    - Loan Name: {loan.loan_name}
    - Type: {loan.loan_type}
    - Interest Rate: {loan.interest_rate}%
    - Outstanding Balance: Rs. {loan.outstanding_amount:.2f}
    - Overdue Period: {loan.overdue_months} months
    
    Rule-based baseline:
    - Suggested Settlement: {rule_results['suggested_settlement_pct']}% (Borrower pays {rule_results['predicted_amount']:.2f})
    
    Return your response as a JSON string with the following keys. Do not include markdown wraps (like ```json). Just return the JSON object:
    - suggested_settlement_pct: float (the percentage the borrower should pay, e.g. 45.5)
    - predicted_amount: float (outstanding * percentage / 100)
    - repayment_recommendation: string (personalized settlement or payment plan recommendation)
    - priority_level: string ("High", "Medium", "Low")
    - risk_analysis: string (analysis of risk of litigation, harassment, or credit score damage)
    - negotiation_tips: string (specific tips for negotiating with {loan.bank})
    """
    
    ai_response = call_gemini(prompt)
    if ai_response:
        try:
            # Strip markdown quotes if AI returned them
            clean_response = ai_response.strip().strip("`").replace("json", "").strip()
            data = json.loads(clean_response)
            return {
                "suggested_settlement_pct": float(data.get("suggested_settlement_pct", rule_results["suggested_settlement_pct"])),
                "predicted_amount": float(data.get("predicted_amount", rule_results["predicted_amount"])),
                "repayment_recommendation": data.get("repayment_recommendation", "Consider one-time settlement using available lump sum."),
                "priority_level": data.get("priority_level", rule_results["priority_level"]),
                "risk_analysis": data.get("risk_analysis", "The account is in overdue status and may be forwarded to collection agencies."),
                "negotiation_tips": data.get("negotiation_tips", "Be polite but firm about your financial constraints. Ask for interest waiver.")
            }
        except Exception as e:
            print(f"Failed to parse Gemini response as JSON: {e}. Falling back to rule engine.")
            
    # Fallback response
    return {
        "suggested_settlement_pct": rule_results["suggested_settlement_pct"],
        "predicted_amount": rule_results["predicted_amount"],
        "repayment_recommendation": f"Initiate a One-Time Settlement (OTS) proposal with {loan.bank}. Request interest waivers.",
        "priority_level": rule_results["priority_level"],
        "risk_analysis": f"At {loan.overdue_months} months overdue, {loan.bank} is likely to engage recovery agents. A settlement is highly recommended to avoid litigation.",
        "negotiation_tips": f"1. Explain that your lump sum is a one-time assistance from family.\n2. Insist on a written OTS agreement before paying.\n3. Request credit status update as 'Settled'."
    }

def get_ai_negotiation_strategy(user: User, profile: Optional[FinancialProfile], loans: List[Loan], health_metrics: Dict[str, Any]) -> str:
    """Generate complete step-by-step debt relief strategy for all loans."""
    loans_str = "\n".join([
        f"- {loan.loan_name} ({loan.loan_type}) at {loan.bank}: Rs. {loan.outstanding_amount:.2f} outstanding, {loan.overdue_months} months overdue."
        for loan in loans
    ])
    
    prompt = f"""
    You are a Senior Debt Settlement Specialist. Design a personalized financial recovery strategy.
    
    FINANCIAL PROFILE:
    - Monthly Income: Rs. {health_metrics['income']:.2f}
    - Monthly Expenses: Rs. {health_metrics['expenses']:.2f}
    - Lump Sum Available: Rs. {health_metrics['lump_sum']:.2f}
    - Total Savings: Rs. {health_metrics['savings']:.2f}
    - Goals: {profile.financial_goals if profile else 'Not specified'}
    
    LOANS PORTFOLIO:
    {loans_str}
    
    Format the strategy in Markdown. Include:
    1. Financial Snapshot & Debt Stress analysis
    2. Allocation recommendation for the lump sum of Rs. {health_metrics['lump_sum']:.2f} (which loans to pay first and why)
    3. Talking points for recovery calls
    4. Practical budgeting tips to maximize monthly surplus (currently Rs. {health_metrics['monthly_surplus']:.2f})
    5. A 30-60-90 day debt-free action plan.
    """
    
    strategy = call_gemini(prompt)
    if strategy:
        return strategy
        
    # Fallback
    fallback = f"""### 📊 PERSONALIZED DEBT RECOVERY STRATEGY (Fallback Mode)

**1. Debt Stress & Stability Snapshot**
- **Debt-to-Income (DTI) Ratio**: {health_metrics['dti_ratio']}%
- **EMI-to-Income Ratio**: {health_metrics['emi_ratio']}%
- **Risk Category**: {health_metrics['risk_category']}
- **Stability Score**: {health_metrics['financial_stability_score']}/100

**2. Lump Sum Allocation Plan**
- Since you have a lump sum of **Rs. {health_metrics['lump_sum']:.2f}** available:
  - Prioritize unsecured high-interest credit cards or personal loans that are overdue by 3+ months.
  - Settle loans with higher overdue periods first to stop escalation.

**3. Budgeting & Surplus Management**
- Your current monthly surplus is **Rs. {health_metrics['monthly_surplus']:.2f}**.
- Try to allocate at least 50% of this surplus to build your settlement fund or savings (currently at **Rs. {health_metrics['savings']:.2f}**).

**4. Lender Talking Points**
- Communicate your genuine hardship (unemployment, medical issues, business loss).
- Always ask for an interest waiver and written OTS agreement prior to payment.

**5. 30-60-90 Day Action Plan**
- **Day 1-30**: Reach out to high-priority lenders requesting one-time settlement terms.
- **Day 31-60**: Negotiate rates down to 40-50% for unsecured debts. Secure OTS letters.
- **Day 61-90**: Complete payments, receive NOCs, and verify credit bureau records.
"""
    return fallback

def get_ai_negotiation_letter(user: User, profile: Optional[FinancialProfile], loan: Loan, settlement_pct: float, predicted_amount: float) -> str:
    """Generate formal legal/negotiation settlement request letter using Gemini."""
    prompt = f"""
    You are a Debt Settlement Lawyer. Draft a professional, legally-sound One-Time Settlement (OTS) proposal letter.
    
    BORROWER DETAILS:
    - Name: {user.name or 'Borrower'}
    - Email: {user.email}
    - Phone: {profile.phone if profile else 'N/A'}
    - Occupation: {profile.occupation if profile else 'N/A'}
    
    LOAN DETAILS:
    - Bank/Lender: {loan.bank}
    - Loan Name: {loan.loan_name}
    - Account ID / Loan ID: {loan.id}
    - Outstanding Amount: Rs. {loan.outstanding_amount:.2f}
    - Overdue Months: {loan.overdue_months} months
    
    PROPOSAL DETAILS:
    - Settlement Percentage: {settlement_pct}%
    - Proposed Settlement Amount: Rs. {predicted_amount:.2f}
    
    Structure the letter with a proper header, formal subject, description of extreme financial hardship (e.g. income drop, medical problems), proposal details, conditions of settlement (full write-off, credit report status as 'Settled', NOC within 30 days), and professional closing.
    """
    
    letter = call_gemini(prompt)
    if letter:
        return letter
        
    # Fallback
    return f"""Date: {func.now()}
To,
The Settlement Department,
{loan.bank}

Subject: Request for One-Time Settlement (OTS) - Loan Account No. {loan.id}

Dear Sir/Madam,

I am writing to formally request a One-Time Settlement (OTS) for my outstanding loan account: {loan.loan_name} (Account No. {loan.id}).

Due to unexpected financial hardships, including a mismatch between my income and essential expenses, I have fallen behind on my payments by {loan.overdue_months} months. My current outstanding balance stands at Rs. {loan.outstanding_amount:,.2f}.

I have managed to arrange a lump sum of Rs. {predicted_amount:,.2f} through family assistance. I propose this amount as a final and complete settlement, representing approximately {int(settlement_pct)}% of the outstanding dues.

Please consider this request on compassionate grounds. If accepted, I request:
1. Written confirmation of the OTS terms before payment.
2. Complete waiver of all penalty interest and charges.
3. Issuance of a No Objection Certificate (NOC) within 30 days of payment.
4. Reporting the loan as "Settled" with zero balance to CIBIL and other credit registries.

Thank you for your understanding.

Sincerely,

{user.name or 'Borrower'}
Email: {user.email}
Phone: {profile.phone if profile else 'N/A'}
"""

def get_ai_financial_advice(user: User, profile: Optional[FinancialProfile], loans: List[Loan], health_metrics: Dict[str, Any], advice_type: str) -> str:
    """Generate strategic advisor recommendations for Budgeting, Savings, Emergency Fund, etc."""
    prompt = f"""
    You are a Certified Financial Planner. Provide expert advice on the topic: '{advice_type}'.
    
    BORROWER PROFILE:
    - Monthly Income: Rs. {health_metrics['income']:.2f}
    - Monthly Expenses: Rs. {health_metrics['expenses']:.2f}
    - Monthly Surplus: Rs. {health_metrics['monthly_surplus']:.2f}
    - Savings: Rs. {health_metrics['savings']:.2f}
    - Total Debt: Rs. {health_metrics['total_outstanding']:.2f}
    
    Deliver professional, specific, and actionable suggestions tailored to this user's situation. Format as Markdown.
    """
    
    advice = call_gemini(prompt)
    if advice:
        return advice
        
    # Fallback
    fallbacks = {
        "Budgeting": f"### 📝 Budgeting Suggestions\n- Use a 50/30/20 budget framework adjusted for debt relief: 50% for Needs, 0% for Wants, 50% for Debt settlement.\n- Reduce monthly expenses of Rs. {health_metrics['expenses']:.2f} by auditing bank statements for subscription cancellations.",
        "Debt Reduction": f"### 📉 Debt Reduction Strategy\n- Settle the highest-interest loans first (Debt Avalanche).\n- Leverage your monthly surplus of Rs. {health_metrics['monthly_surplus']:.2f} to build a negotiation fund.",
        "Savings": f"### 💰 Savings Planning\n- Automate transfers of Rs. 1000-5000 from monthly income to a separate account immediately on receipt.\n- Your current savings are Rs. {health_metrics['savings']:.2f}. Try to grow this to cover 3 months of basic expenses.",
        "EMI Optimization": f"### 📊 EMI Optimization\n- Ask your lenders for longer loan tenures to decrease the current EMI of Rs. {health_metrics['total_emi']:.2f}.\n- Consolidate multiple loans into a single lower-interest personal loan if your credit score allows.",
        "Investment": f"### 📈 Investment Guidance\n- Avoid high-risk investments (crypto, stocks) while in debt distress.\n- Keep your funds in high-yield savings accounts or liquid mutual funds to remain liquid for settlements.",
        "Emergency Fund": f"### 🚨 Emergency Fund Blueprint\n- Aim for a starter emergency fund of Rs. 25,000 immediately.\n- Keep this fund completely separate from your debt-settlement lump sum of Rs. {health_metrics['lump_sum']:.2f}."
    }
    return fallbacks.get(advice_type, "Focus on building a monthly surplus and negotiating settlements with your lenders.")
