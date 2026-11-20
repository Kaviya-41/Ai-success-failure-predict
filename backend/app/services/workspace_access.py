from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.workspace import WorkspaceMember


@dataclass(frozen=True)
class WorkspaceAccess:
    workspace_id: int
    role: str

    @property
    def can_manage_members(self) -> bool:
        return self.role in {"owner", "manager"}

    @property
    def can_delete_records(self) -> bool:
        return self.role in {"owner", "manager"}


def get_workspace_access(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    selected_workspace_id: Optional[int] = Header(default=None, alias="X-Workspace-ID"),
) -> WorkspaceAccess:
    memberships = db.query(WorkspaceMember).filter(
        WorkspaceMember.user_id == current_user.id
    )
    if selected_workspace_id is not None:
        membership = memberships.filter(
            WorkspaceMember.workspace_id == selected_workspace_id
        ).first()
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this workspace.",
            )
    else:
        membership = memberships.order_by(WorkspaceMember.id.asc()).first()
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is not associated with a workspace.",
            )
    return WorkspaceAccess(workspace_id=membership.workspace_id, role=membership.role)


def require_workspace_manager(access: WorkspaceAccess) -> None:
    if not access.can_manage_members:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace owner or manager permissions are required.",
        )


def require_workspace_record_manager(access: WorkspaceAccess) -> None:
    if not access.can_delete_records:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace owner or manager permissions are required for this action.",
        )
