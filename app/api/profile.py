import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import User, FinancialProfile
from app.schemas import schemas
from app.auth.auth_handler import get_current_user
from app.utils.audit import log_action

router = APIRouter(prefix="/api/profile", tags=["User Profile"])

@router.get("", response_model=schemas.FinancialProfileResponse)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).first()
    if not profile:
        profile = FinancialProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

@router.put("", response_model=schemas.FinancialProfileResponse)
def update_profile(
    profile_data: schemas.FinancialProfileUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).first()
    if not profile:
        profile = FinancialProfile(user_id=current_user.id)
        db.add(profile)
        
    for key, value in profile_data.model_dump().items():
        setattr(profile, key, value)
        
    db.commit()
    db.refresh(profile)
    
    log_action(db, "Update Profile", f"Financial profile updated for: {current_user.email}", user_id=current_user.id, request=request)
    return profile

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate file extension
    allowed_extensions = ["jpg", "jpeg", "png", "webp"]
    file_ext = file.filename.split(".")[-1].lower() if file.filename else ""
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension. Allowed formats: {', '.join(allowed_extensions)}"
        )
        
    # Create static avatars directory inside workspace
    static_dir = os.path.join("C:\\Users\\varun\\.gemini\\antigravity\\scratch\\FinReliefAI\\backend", "static", "avatars")
    os.makedirs(static_dir, exist_ok=True)
    
    file_name = f"avatar_{current_user.id}.{file_ext}"
    file_path = os.path.join(static_dir, file_name)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save avatar file: {e}"
        )
        
    avatar_url = f"/static/avatars/{file_name}"
    
    # Save or update avatar record in a profile column or just return the URL
    log_action(db, "Upload Avatar", f"Avatar uploaded: {avatar_url}", user_id=current_user.id)
    return {"avatar_url": avatar_url}
