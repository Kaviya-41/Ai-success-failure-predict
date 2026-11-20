"""
API endpoint for GitHub repository analysis.
"""

from datetime import date, datetime, time, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.activity_log import ActivityLog
from app.models.github_analysis_report import GitHubAnalysisReport
from app.models.project import Project
from app.models.user import User
from app.services.github_analysis_service import GitHubAPIError
from app.services.github_analysis_service import GitHubAnalysisService
from app.services.github_analysis_quota import consume_github_analysis_quota
from app.services.workspace_access import WorkspaceAccess, get_workspace_access

router = APIRouter(prefix="/github", tags=["GitHub"])


class GitHubAnalysisRequest(BaseModel):
    repository_url: str
    project_id: Optional[int] = None


@router.post("/analyze")
def analyze_github_repository(
    payload: GitHubAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    access: WorkspaceAccess = Depends(get_workspace_access),
):
    """Analyze a public GitHub repository and evaluate project delivery risk."""
    repository_url = payload.repository_url.strip()

    if not repository_url:
        raise HTTPException(status_code=400, detail="Please enter a valid GitHub repository URL.")

    if payload.project_id:
        project = db.query(Project).filter(
            Project.id == payload.project_id,
            Project.workspace_id == access.workspace_id,
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    consume_github_analysis_quota(
        db,
        user_id=current_user.id,
        workspace_id=access.workspace_id,
    )

    try:
        analysis_result = GitHubAnalysisService.analyze_repository(repository_url)
    except GitHubAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Repository analysis could not be completed. Please try again.") from exc

    decision_metrics = analysis_result["metrics"]
    project_metrics = GitHubAnalysisService.to_project_metrics(decision_metrics)
    decision = GitHubAnalysisService.build_rule_prediction(decision_metrics)

    response_data = {
        "status": "success",
        "repository_url": repository_url,
        "repository": analysis_result.get("repository", {}),
        "metrics": decision_metrics,
        "project_metrics": project_metrics,
        "prediction": decision["prediction"],
        "success_probability": decision["success_probability"],
        "failure_probability": decision["failure_probability"],
        "risk_score": decision["risk_score"],
        "health_score": decision["health_score"],
        "risk_level": decision["risk_level"],
        "risk_factors": decision["risk_factors"],
        "positive_factors": decision["positive_factors"],
        "recommendations": decision["recommendations"],
        "recovery_plan": decision.get("recovery_plan", []),
        "motivation": decision.get("motivation", ""),
        "success_conditions": decision["success_conditions"],
        "failure_conditions": decision["failure_conditions"],
        "total_conditions": decision["total_conditions"],
        "message": "Repository analysis completed successfully.",
    }

    repository_name = response_data["repository"].get("repository_name") or ""
    parsed_url = GitHubAnalysisService.parse_repository_url(repository_url)
    report = GitHubAnalysisReport(
        user_id=current_user.id,
        workspace_id=access.workspace_id,
        repository_url=repository_url,
        original_repository_url=repository_url,
        repository_owner=parsed_url["owner"],
        repository_name=repository_name,
        prediction=decision["prediction"],
        health_score=decision["health_score"],
        risk_score=decision["risk_score"],
        risk_level=decision["risk_level"],
        report_data=response_data,
    )
    db.add(report)
    try:
        db.flush()
        response_data["report_id"] = report.id
        response_data["created_at"] = report.created_at.isoformat()
        report.report_data = response_data
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Repository analysis completed, but its report could not be saved.",
        ) from exc

    if payload.project_id:
        log = ActivityLog(
            action="analyze_github",
            details=f"Analyzed GitHub repository {repository_url}",
            user_id=current_user.id,
        )
        db.add(log)
        db.commit()

    return response_data


@router.get("/reports")
def list_github_analysis_reports(
    limit: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None, max_length=200),
    prediction: Optional[str] = Query(default=None, pattern="^(SUCCESS|FAILURE|Success|Failure)$"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(get_workspace_access),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from must not be after date_to.")
    query = db.query(GitHubAnalysisReport).filter(
        GitHubAnalysisReport.workspace_id == access.workspace_id
    )
    if search:
        escaped = search.replace("%", r"\%").replace("_", r"\_")
        query = query.filter(
            GitHubAnalysisReport.repository_name.ilike(f"%{escaped}%")
            | GitHubAnalysisReport.repository_url.ilike(f"%{escaped}%")
        )
    if prediction:
        query = query.filter(
            GitHubAnalysisReport.prediction.ilike(prediction)
        )
    if date_from:
        query = query.filter(
            GitHubAnalysisReport.created_at >= datetime.combine(date_from, time.min)
        )
    if date_to:
        query = query.filter(
            GitHubAnalysisReport.created_at < datetime.combine(
                date_to + timedelta(days=1), time.min
            )
        )
    reports = query.order_by(GitHubAnalysisReport.created_at.desc()).limit(limit).all()
    return {
        "reports": [
            {
                "id": report.id,
                "repository_url": report.repository_url,
                "repository_owner": report.repository_owner,
                "repository_name": report.repository_name,
                "prediction": report.prediction,
                "health_score": report.health_score,
                "risk_score": report.risk_score,
                "risk_level": report.risk_level,
                "created_at": report.created_at.isoformat(),
            }
            for report in reports
        ]
    }


@router.get("/reports/{report_id}")
def get_github_analysis_report(
    report_id: int,
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(get_workspace_access),
):
    query = db.query(GitHubAnalysisReport).filter(
        GitHubAnalysisReport.id == report_id,
        GitHubAnalysisReport.workspace_id == access.workspace_id,
    )
    report = query.first()
    if not report:
        raise HTTPException(status_code=404, detail="GitHub analysis report not found")
    return report.report_data


@router.get("/repository/{project_id}")
def get_repository_analysis(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    access: WorkspaceAccess = Depends(get_workspace_access),
):
    """Get a previously stored project analysis if one exists."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.workspace_id == access.workspace_id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "message": "GitHub repository analysis is available on the project analysis page.",
        "project_id": project_id,
    }
