import io
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.services.ml_service import MLService
from app.services.recommendation_service import RecommendationService
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports")

@router.get("/pdf/{project_id}")
def export_project_pdf(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates and streams a PDF risk analysis report for a single project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough privileges")
        
    # Re-evaluate features to get recommendations and SHAP factors
    metrics = {
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
        prediction = MLService.predict_single(metrics)
        recs = RecommendationService.generate_recommendations(metrics)
        prediction["recommendations"] = recs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compile PDF prediction: {str(e)}")
        
    pdf_bytes = ReportService.generate_project_pdf(project, prediction)
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=project_report_{project_id}.pdf"}
    )

@router.get("/excel")
def export_projects_excel(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates and streams an Excel sheet summarizing all projects."""
    query = db.query(Project)
    if current_user.role != "admin":
        query = query.filter(Project.owner_id == current_user.id)
        
    projects = query.all()
    if not projects:
        raise HTTPException(status_code=400, detail="No projects found to export")
        
    excel_bytes = ReportService.generate_excel_report(projects)
    
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=projects_summary.xlsx"}
    )
