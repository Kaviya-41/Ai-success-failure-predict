from datetime import datetime
from typing import Dict

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models.github_analysis_report import GitHubAnalysisReport
from app.models.prediction_history import GitHubRepository
from app.models.project import Project
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember


def _add_missing_columns(engine: Engine, table_name: str, definitions: Dict[str, str]) -> None:
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns(table_name)}
    with engine.begin() as connection:
        for column_name, definition in definitions.items():
            if column_name not in existing:
                connection.execute(
                    text(f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {definition}')
                )


def upgrade_workspace_schema(engine: Engine) -> None:
    """Idempotently add workspace ownership and backfill existing records in place."""
    _add_missing_columns(
        engine,
        "projects",
        {
            "description": "TEXT",
            "workspace_id": "INTEGER REFERENCES workspaces(id)",
            "updated_at": "TIMESTAMP",
        },
    )
    _add_missing_columns(
        engine,
        "github_analysis_reports",
        {
            "workspace_id": "INTEGER REFERENCES workspaces(id)",
            "repository_owner": "VARCHAR",
            "original_repository_url": "VARCHAR",
        },
    )
    _add_missing_columns(
        engine,
        "github_repositories",
        {"workspace_id": "INTEGER REFERENCES workspaces(id)"},
    )

    session = Session(bind=engine)
    try:
        user_workspace: Dict[int, int] = {}
        users = session.query(User).order_by(User.id.asc()).all()
        for user in users:
            membership = (
                session.query(WorkspaceMember)
                .filter(WorkspaceMember.user_id == user.id)
                .order_by(WorkspaceMember.id.asc())
                .first()
            )
            if membership is None:
                workspace_name = f"{(user.full_name or user.email.split('@')[0]).strip()}'s Workspace"
                workspace = Workspace(name=workspace_name[:120], created_by=user.id)
                session.add(workspace)
                session.flush()
                member_role = {
                    "admin": "owner",
                    "manager": "manager",
                }.get(user.role, "member")
                membership = WorkspaceMember(
                    workspace_id=workspace.id,
                    user_id=user.id,
                    role=member_role,
                )
                session.add(membership)
                session.flush()
            user_workspace[user.id] = membership.workspace_id

        for project in session.query(Project).all():
            if project.workspace_id is None:
                project.workspace_id = user_workspace.get(project.owner_id)
            if project.description is None:
                project.description = ""
            if project.updated_at is None:
                project.updated_at = project.created_at or datetime.utcnow()

        for report in session.query(GitHubAnalysisReport).all():
            if report.workspace_id is None:
                report.workspace_id = user_workspace.get(report.user_id)
            if not report.original_repository_url:
                report.original_repository_url = report.repository_url
            if not report.repository_owner:
                report.repository_owner = report.repository_name.split("/", 1)[0]

        projects = {project.id: project for project in session.query(Project).all()}
        for repository in session.query(GitHubRepository).all():
            if repository.workspace_id is None:
                project = projects.get(repository.project_id)
                if project is not None:
                    repository.workspace_id = project.workspace_id

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
