# FinRelief AI – AI Powered Debt Relief & Financial Recovery Platform

FinRelief AI is an enterprise-grade, full-stack application designed to help borrowers manage debt profiles, compute stress metrics, leverage Google Gemini AI for one-time settlements and strategic planning, draft legal settlement proposals, and consult financial advisor agents.

---

## 🏛️ System Architecture

```mermaid
graph TD
    subgraph Frontend [React Single Page Application]
        UI[Tailwind & CSS Variables UI]
        State[Auth & Notification Providers]
        Client[Axios API Client + Refresh Interceptor]
    end

    subgraph Backend [FastAPI REST Service]
        Main[FastAPI App Gateway]
        Middleware[Rate Limiter & RBAC Middleware]
        Auth[JWT Session & Hashing Manager]
        Controllers[API Routers]
        Calc[Financial Health Engine]
        PDF[PDF Report Generator]
        AI[Gemini AI Interface]
    end

    subgraph Database [Relational Data Store]
        DB[(SQLite / PostgreSQL)]
    end

    UI --> State
    State --> Client
    Client -- HTTP Requests --> Main
    Main --> Middleware
    Middleware --> Controllers
    Controllers --> Auth
    Controllers --> Calc
    Controllers --> PDF
    Controllers --> AI
    Controllers --> DB
    AI -- Google API --> Gemini[Gemini-1.5-Flash Model]
```

---

## 📊 Relational Database Schema (ERD)

```mermaid
erDiagram
    USERS ||--|| FINANCIAL_PROFILES : owns
    USERS ||--o{ LOANS : manages
    USERS ||--o{ AI_HISTORY : audits
    USERS ||--o{ SETTLEMENT_PREDICTIONS : receives
    USERS ||--o{ NEGOTIATION_LETTERS : drafts
    USERS ||--o{ RECOMMENDATIONS : follows
    USERS ||--o{ NOTIFICATIONS : reviews
    USERS ||--o{ AUDIT_LOGS : records

    USERS {
        int id PK
        string name
        string email UK
        string password_hash
        string role
        datetime created_at
    }

    FINANCIAL_PROFILES {
        int id PK
        int user_id FK
        string phone
        string occupation
        float monthly_income
        float monthly_expenses
        float lump_sum_available
        float savings
        text financial_goals
    }

    LOANS {
        int id PK
        int user_id FK
        string loan_name
        string bank
        string loan_type
        float interest_rate
        float outstanding_amount
        float monthly_emi
        int overdue_months
        string status
    }

    SETTLEMENT_PREDICTIONS {
        int id PK
        int loan_id FK
        int user_id FK
        float suggested_settlement_pct
        float predicted_amount
        text repayment_recommendation
        string priority_level
        text risk_analysis
        text negotiation_tips
    }

    AI_HISTORY {
        int id PK
        int user_id FK
        text prompt
        text response
        string query_type
        datetime created_at
    }

    NEGOTIATION_LETTERS {
        int id PK
        int loan_id FK
        int user_id FK
        text letter_content
        datetime created_at
    }
```

---

## 🚀 Installation & Local Setup

### Prerequisite Environment
- Python 3.11+
- Node.js 18+ (for local frontend installation, optional if running Docker)

### 1. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Define environment variables in a `.env` file:
   ```env
   SECRET_KEY=supersecretkeyforfinreliefai123access
   REFRESH_SECRET_KEY=supersecretkeyforfinreliefai123refresh
   DATABASE_URL=sqlite:///./finrelief.db
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
5. Run the server from the root directory:
   ```bash
   python run.py
   ```
   Or from the backend directory:
   ```bash
   uvicorn app.main:app --reload
   ```
   API Docs will be available at `http://127.0.0.1:8000/docs`.

### 2. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

## 🐳 Docker Deployment

To launch the complete application stack (React frontend, FastAPI backend, and a production PostgreSQL database), run:
```bash
docker-compose up --build
```
- **Frontend URL**: `http://localhost`
- **Backend API URL**: `http://localhost/api`
- **PostgreSQL Database**: Port `5432`

---

## 🔒 Security Features Implemented
1. **Password Protection**: Salted PBKDF2 hashes using SHA-256 standard library implementations (NIST & OWASP compliant).
2. **Access Security**: Decoupled JWT access tokens (120 minutes expiry) and refresh tokens (7 days expiry).
3. **Brute Force Protection**: Rate limiting middleware tracking requests by client IP.
4. **Input Validation**: Strict schema matching and type safety powered by Pydantic.
5. **RBAC**: Guarded routes verifying admin status prior to analytics disclosure.
