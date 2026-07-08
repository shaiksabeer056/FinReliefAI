from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Dict, Any
from app.database.connection import get_db
from app.models.models import AIHistory, User
from app.schemas import schemas
from app.auth.auth_handler import get_current_user
from app.utils.audit import log_action
import csv
from io import StringIO

router = APIRouter(prefix="/api/history", tags=["History Management"])

@router.get("", response_model=Dict[str, Any] if False else Any)
def get_user_history(
    search: Optional[str] = Query(None, description="Search prompts or responses"),
    query_type: Optional[str] = Query(None, description="Filter by query type"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(AIHistory).filter(AIHistory.user_id == current_user.id)
    
    if query_type:
        query = query.filter(AIHistory.query_type == query_type)
        
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                AIHistory.prompt.ilike(search_filter),
                AIHistory.response.ilike(search_filter),
                AIHistory.query_type.ilike(search_filter)
            )
        )
        
    total = query.count()
    
    # Order by timestamp desc
    history_items = query.order_by(AIHistory.created_at.desc())\
        .offset((page - 1) * limit)\
        .limit(limit)\
        .all()
        
    response_items = [{
        "id": item.id,
        "query_type": item.query_type,
        "prompt": item.prompt,
        "response": item.response,
        "created_at": item.created_at
    } for item in history_items]
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": response_items
    }

@router.delete("/{history_id}")
def delete_history_item(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = db.query(AIHistory).filter(AIHistory.id == history_id, AIHistory.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="History item not found")
        
    db.delete(item)
    db.commit()
    
    log_action(db, "Delete History", f"Deleted AI History item ID: {history_id}", user_id=current_user.id)
    return {"message": "History item deleted successfully"}

@router.get("/export/csv")
def export_history_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    history_items = db.query(AIHistory)\
        .filter(AIHistory.user_id == current_user.id)\
        .order_by(AIHistory.created_at.desc())\
        .all()
        
    # Generate CSV in memory
    f = StringIO()
    writer = csv.writer(f)
    
    # Header
    writer.writerow(["ID", "Timestamp", "Query Type", "Prompt", "AI Response"])
    
    # Rows
    for item in history_items:
        writer.writerow([
            item.id,
            item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else "",
            item.query_type,
            item.prompt,
            item.response
        ])
        
    f.seek(0)
    
    # Return as StreamingResponse
    return StreamingResponse(
        StringIO(f.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=finrelief_ai_history.csv"}
    )
