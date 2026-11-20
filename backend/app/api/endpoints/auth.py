from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.api.deps import get_current_user
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.user import UserCreate, UserUpdate, UserOut, Token

router = APIRouter(prefix="/auth")

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Registers a new user. The very first user created in the database is automatically assigned the Admin role."""
    # Check if email exists
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # The first account owns the workspace; public registration cannot create admins.
    user_count = db.query(User).count()
    role = "admin" if user_count == 0 else ("manager" if user_in.role == "manager" else "member")
    
    hashed_pwd = get_password_hash(user_in.password)
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        full_name=user_in.full_name,
        role=role,
        is_active=True,
        is_verified=True # Auto-verify for easy local demo
    )
    db.add(new_user)
    db.flush()
    workspace = Workspace(
        name=f"{(new_user.full_name or new_user.email.split('@')[0]).strip()}'s Workspace"[:120],
        created_by=new_user.id,
    )
    db.add(workspace)
    db.flush()
    db.add(WorkspaceMember(
        workspace_id=workspace.id,
        user_id=new_user.id,
        role="owner",
    ))
    db.commit()
    db.refresh(new_user)
    
    # Audit log
    log = ActivityLog(action="register", details=f"User {new_user.email} registered", user_id=new_user.id)
    db.add(log)
    db.commit()
    
    return new_user

@router.post("/login", response_model=Token)
def login(user_in: UserCreate, db: Session = Depends(get_db)):
    """Authenticates a user via JSON payload and issues a JWT access token."""
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token = create_access_token(subject=user.id)
    
    # Audit log
    log = ActivityLog(action="login", details=f"User {user.email} logged in", user_id=user.id)
    db.add(log)
    db.commit()
    
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.post("/login-form", response_model=Token)
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticates a user via OAuth2 Form data (used by Swagger UI/FastAPI OpenAPI docs)."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.get("/profile", response_model=UserOut)
def read_profile(current_user: User = Depends(get_current_user)):
    """Returns details of the currently authenticated user."""
    return current_user

@router.put("/profile", response_model=UserOut)
def update_profile(user_in: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Updates user information (email, full name, or password)."""
    if user_in.email:
        existing = db.query(User).filter(User.email == user_in.email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = user_in.email
    if user_in.full_name:
        current_user.full_name = user_in.full_name
    if user_in.password:
        current_user.hashed_password = get_password_hash(user_in.password)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
