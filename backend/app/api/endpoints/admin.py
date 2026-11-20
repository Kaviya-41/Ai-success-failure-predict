from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.api.deps import get_current_active_admin, get_current_active_manager
from app.models.user import User
from app.models.project import Project
from app.models.activity_log import ActivityLog
from app.models.model_metadata import ModelMetadata
from app.schemas.user import UserOut

router = APIRouter(prefix="/admin")

@router.get("/users", response_model=List[UserOut])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """Admin-only endpoint to list all users in the system."""
    return db.query(User).order_by(User.created_at.desc()).all()

@router.put("/users/{id}/role", response_model=UserOut)
def update_user_role(
    id: int,
    role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """Admin-only endpoint to change a user's role (admin, manager, member)."""
    if role not in ["admin", "manager", "member"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be admin, manager, or member")
        
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.role = role
    db.commit()
    db.refresh(user)
    
    # Audit log
    log = ActivityLog(action="change_role", details=f"Changed user {user.email} role to {role}", user_id=current_user.id)
    db.add(log)
    db.commit()
    
    return user

@router.get("/activity-logs")
def get_activity_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_manager),
    limit: int = 100,
    offset: int = 0
):
    """Manager/Admin endpoint to view activity and audit logs."""
    logs = db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).offset(offset).limit(limit).all()
    result = []
    for l in logs:
        user = db.query(User).filter(User.id == l.user_id).first()
        result.append({
            "id": l.id,
            "action": l.action,
            "details": l.details,
            "timestamp": l.timestamp,
            "user_email": user.email if user else "Unknown"
        })
    return result

@router.get("/system-analytics")
def get_system_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_manager)
):
    """Retrieves system-wide analytics for dashboard and admin monitoring."""
    total_users = db.query(User).count()
    total_projects = db.query(Project).count()
    active_projects = db.query(Project).filter(Project.is_archived == False).count()
    
    high_risk_projects = db.query(Project).filter(Project.risk_level == "High", Project.is_archived == False).count()
    med_risk_projects = db.query(Project).filter(Project.risk_level == "Medium", Project.is_archived == False).count()
    low_risk_projects = db.query(Project).filter(Project.risk_level == "Low", Project.is_archived == False).count()
    
    success_predictions = db.query(Project).filter(Project.is_successful_prediction == True).count()
    failed_predictions = db.query(Project).filter(Project.is_successful_prediction == False).count()
    
    active_model = db.query(ModelMetadata).filter(ModelMetadata.is_active == True).first()
    
    return {
        "total_users": total_users,
        "total_projects": total_projects,
        "active_projects": active_projects,
        "high_risk_projects": high_risk_projects,
        "med_risk_projects": med_risk_projects,
        "low_risk_projects": low_risk_projects,
        "predicted_success_count": success_predictions,
        "predicted_failure_count": failed_predictions,
        "active_model_name": active_model.model_name if active_model else "XGBoost",
        "active_model_accuracy": active_model.accuracy if active_model else 0.85
    }
