from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import User, FinancialProfile
from app.schemas import schemas
from app.auth.auth_handler import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    REFRESH_SECRET_KEY,
    get_current_user
)
from app.utils.audit import log_action

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, request: Request, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email.lower().strip()).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_pwd = get_password_hash(user.password)
    
    # Check if there are users; if not, first user can be admin for local testing
    user_count = db.query(User).count()
    role = "admin" if user_count == 0 else user.role or "user"
    
    new_user = User(
        name=user.name,
        email=user.email.lower().strip(),
        password_hash=hashed_pwd,
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Initialize blank financial profile
    new_profile = FinancialProfile(user_id=new_user.id)
    db.add(new_profile)
    db.commit()
    
    log_action(db, "Register", f"User registered: {new_user.email}", user_id=new_user.id, request=request)
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(user_credentials: schemas.UserCreate, request: Request, db: Session = Depends(get_db)):
    email = user_credentials.email.lower().strip()
    password = user_credentials.password
    
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        log_action(db, "Login Failed", f"Failed login attempt for: {email}", request=request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
        
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    log_action(db, "Login", f"User logged in: {user.email}", user_id=user.id, request=request)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=schemas.Token)
def refresh_token(token_input: schemas.RefreshTokenInput, db: Session = Depends(get_db)):
    payload = decode_token(token_input.refresh_token, REFRESH_SECRET_KEY)
    email: str = payload.get("sub")
    token_type: str = payload.get("type")
    
    if email is None or token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
        
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
        
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=schemas.UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user

@router.post("/forgot-password")
def forgot_password(payload: dict, db: Session = Depends(get_db)):
    email = payload.get("email", "").lower().strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Prevent user enumeration by returning success anyway
        return {"message": "If the email is registered, a reset link will be simulated."}
        
    # Simulated recovery token or system log
    log_action(db, "Forgot Password Request", f"Requested for: {email}", user_id=user.id)
    return {"message": "Recovery token generated successfully. For testing, token is 'RESET_TOKEN_123'"}

@router.post("/reset-password")
def reset_password(payload: dict, db: Session = Depends(get_db)):
    email = payload.get("email", "").lower().strip()
    token = payload.get("token", "")
    new_password = payload.get("new_password", "")
    
    if not email or not token or not new_password:
        raise HTTPException(status_code=400, detail="Missing required parameters")
        
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Validation of simulated token
    if token != "RESET_TOKEN_123":
        raise HTTPException(status_code=400, detail="Invalid password recovery token")
        
    user.password_hash = get_password_hash(new_password)
    db.commit()
    
    log_action(db, "Reset Password", f"Password reset successful for: {email}", user_id=user.id)
    return {"message": "Password reset successfully. You can now login with your new password."}
