import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database.connection import Base, get_db
import os

# Use a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_finrelief.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables and remove file
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_finrelief.db"):
        try:
            os.remove("./test_finrelief.db")
        except Exception:
            pass

client = TestClient(app)

def test_register():
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123", "name": "Test User"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_login():
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_get_profile():
    # Login to get token
    login_response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Get profile
    response = client.get(
        "/api/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["monthly_income"] == 0.0

def test_loan_crud():
    # Login to get token
    login_response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Create loan
    create_response = client.post(
        "/api/loans",
        json={
            "loan_name": "Test Personal Loan",
            "bank": "HDFC Bank",
            "loan_type": "Personal Loan",
            "interest_rate": 12.5,
            "outstanding_amount": 150000.0,
            "monthly_emi": 8500.0,
            "overdue_months": 3
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 201
    loan_id = create_response.json()["id"]
    
    # List loans
    list_response = client.get(
        "/api/loans",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    
    # Delete loan
    delete_response = client.delete(
        f"/api/loans/{loan_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_response.status_code == 200
