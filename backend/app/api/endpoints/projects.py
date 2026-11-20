from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.activity_log import ActivityLog
from app.models.notification import Notification
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut
from app.services.ml_service import MLService
from app.services.recommendation_service import RecommendationService
from app.services.workspace_access import (
    WorkspaceAccess,
    get_workspace_access,
    require_workspace_record_manager,
)

router = APIRouter(prefix="/projects")

@router.get("/", response_model=List[ProjectOut])
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    access: WorkspaceAccess = Depends(get_workspace_access),
    search: Optional[str] = None,
    risk_level: Optional[str] = None,
    project_type: Optional[str] = None,
    is_archived: bool = False,
    limit: int = 100,
    offset: int = 0
):
    """Lists records in the selected authorized workspace."""
    query = db.query(Project).filter(Project.workspace_id == access.workspace_id)
        
    query = query.filter(Project.is_archived == is_archived)
    
    if search:
        query = query.filter(Project.name.ilike(f"%{search}%") | Project.company_name.ilike(f"%{search}%"))
    if risk_level:
        query = query.filter(Project.risk_level == risk_level)
    if project_type:
        query = query.filter(Project.project_type == project_type)
        
    return query.order_by(Project.created_at.desc()).offset(offset).limit(limit).all()

@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    access: WorkspaceAccess = Depends(get_workspace_access),
):
    """Creates a project and automatically runs the active ML model to calculate risks, probabilities, and health score."""
    # Create project object
    # Run automatic ML prediction on the project fields
    input_data = project_in.model_dump()
    try:
        prediction = MLService.predict_single(input_data)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Project prediction could not be calculated; the project was not saved.",
        ) from exc

    project = Project(
        **input_data,
        owner_id=current_user.id,
        workspace_id=access.workspace_id,
        success_probability=prediction["success_probability"],
        failure_probability=prediction["failure_probability"],
        risk_score=prediction["risk_score"],
        risk_level=prediction["risk_level"],
        health_score=prediction["health_score"],
        is_successful_prediction=prediction["is_successful_prediction"],
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Create notification if high risk
    if project.risk_level == "High":
        notif = Notification(
            title="High Risk Project Detected",
            message=f"Project '{project.name}' has been predicted with a High Risk score of {project.risk_score:.1f}/100.",
            type="danger",
            user_id=current_user.id
        )
        db.add(notif)
        db.commit()
        
    # Audit log
    log = ActivityLog(action="create_project", details=f"Created project {project.name}", user_id=current_user.id)
    db.add(log)
    db.commit()
    
    return project

@router.get("/{id}", response_model=ProjectOut)
def get_project_by_id(
    id: int,
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(get_workspace_access),
):
    """Retrieves a single project by ID."""
    project = db.query(Project).filter(
        Project.id == id,
        Project.workspace_id == access.workspace_id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    return project

@router.put("/{id}", response_model=ProjectOut)
def update_project(
    id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    access: WorkspaceAccess = Depends(get_workspace_access),
):
    """Updates a project's parameters and recalculates its risk and success probabilities."""
    project = db.query(Project).filter(
        Project.id == id,
        Project.workspace_id == access.workspace_id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Apply updates
    update_data = project_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
        
    # Re-run ML prediction
    current_metrics = {
        "budget": project.budget,
        "duration_days": project.duration_days,
        "team_size": project.team_size,
        "team_experience_years": project.team_experience_years,
        "project_complexity": project.project_complexity,
        "requirement_changes": project.requirement_changes,
        "sprint_delays": project.sprint_delays,
        "bug_count": project.bug_count,
        "testing_coverage": project.testing_coverage,
        "client_involvement": project.client_involvement,
        "resource_availability": project.resource_availability,
        "customer_satisfaction": project.customer_satisfaction,
        "project_type": project.project_type or "Web"
    }
    
    try:
        prediction = MLService.predict_single(current_metrics)
        project.success_probability = prediction["success_probability"]
        project.failure_probability = prediction["failure_probability"]
        project.risk_score = prediction["risk_score"]
        project.risk_level = prediction["risk_level"]
        project.health_score = prediction["health_score"]
        project.is_successful_prediction = prediction["is_successful_prediction"]
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Project prediction could not be recalculated; changes were not saved.",
        ) from exc
        
    project.updated_at = datetime.utcnow()
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Audit log
    log = ActivityLog(action="update_project", details=f"Updated project {project.name}", user_id=current_user.id)
    db.add(log)
    db.commit()
    
    return project

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    access: WorkspaceAccess = Depends(get_workspace_access),
):
    """Deletes a project."""
    require_workspace_record_manager(access)
    project = db.query(Project).filter(
        Project.id == id,
        Project.workspace_id == access.workspace_id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Audit log
    log = ActivityLog(action="delete_project", details=f"Deleted project {project.name}", user_id=current_user.id)
    db.add(log)
    
    db.delete(project)
    db.commit()
    
    return None

@router.post("/{id}/archive", response_model=ProjectOut)
def archive_project(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    access: WorkspaceAccess = Depends(get_workspace_access),
):
    """Archives a project."""
    project = db.query(Project).filter(
        Project.id == id,
        Project.workspace_id == access.workspace_id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    project.is_archived = True
    project.updated_at = datetime.utcnow()
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Audit log
    log = ActivityLog(action="archive_project", details=f"Archived project {project.name}", user_id=current_user.id)
    db.add(log)
    db.commit()
    
    return project

@router.post("/{id}/unarchive", response_model=ProjectOut)
def unarchive_project(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    access: WorkspaceAccess = Depends(get_workspace_access),
):
    """Restores an archived project."""
    project = db.query(Project).filter(
        Project.id == id,
        Project.workspace_id == access.workspace_id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    project.is_archived = False
    project.updated_at = datetime.utcnow()
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Audit log
    log = ActivityLog(action="unarchive_project", details=f"Unarchived project {project.name}", user_id=current_user.id)
    db.add(log)
    db.commit()
    
    return project
