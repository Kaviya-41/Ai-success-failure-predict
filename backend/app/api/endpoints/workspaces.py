from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.workspace import WorkspaceMemberCreate
from app.services.workspace_access import (
    WorkspaceAccess,
    get_workspace_access,
    require_workspace_manager,
)

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.get("/")
def list_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    memberships = (
        db.query(WorkspaceMember, Workspace)
        .join(Workspace, Workspace.id == WorkspaceMember.workspace_id)
        .filter(WorkspaceMember.user_id == current_user.id)
        .order_by(Workspace.id.asc())
        .all()
    )
    return {
        "workspaces": [
            {
                "id": workspace.id,
                "name": workspace.name,
                "role": membership.role,
                "can_manage_members": membership.role in {"owner", "manager"},
            }
            for membership, workspace in memberships
        ]
    }


@router.get("/members")
def list_workspace_members(
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(get_workspace_access),
):
    memberships = (
        db.query(WorkspaceMember, User)
        .join(User, User.id == WorkspaceMember.user_id)
        .filter(WorkspaceMember.workspace_id == access.workspace_id)
        .order_by(WorkspaceMember.id.asc())
        .all()
    )
    return {
        "members": [
            {
                "id": membership.id,
                "email": member.email,
                "full_name": member.full_name,
                "role": membership.role,
            }
            for membership, member in memberships
        ]
    }


@router.post("/members", status_code=status.HTTP_201_CREATED)
def add_workspace_member(
    payload: WorkspaceMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    access: WorkspaceAccess = Depends(get_workspace_access),
):
    require_workspace_manager(access)
    if access.role == "manager" and payload.role != "member":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Managers can invite members but cannot assign manager roles.",
        )

    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="An active account with that email was not found.",
        )
    if db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == access.workspace_id,
        WorkspaceMember.user_id == user.id,
    ).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That user is already a workspace member.",
        )

    membership = WorkspaceMember(
        workspace_id=access.workspace_id,
        user_id=user.id,
        role=payload.role,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return {
        "id": membership.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": membership.role,
    }


@router.delete("/members/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_workspace_member(
    membership_id: int,
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(get_workspace_access),
):
    require_workspace_manager(access)
    membership = db.query(WorkspaceMember).filter(
        WorkspaceMember.id == membership_id,
        WorkspaceMember.workspace_id == access.workspace_id,
    ).first()
    if membership is None:
        raise HTTPException(status_code=404, detail="Workspace member not found.")
    if membership.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A workspace owner cannot be removed.",
        )
    if access.role == "manager" and membership.role == "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Managers cannot remove other managers.",
        )
    db.delete(membership)
    db.commit()
