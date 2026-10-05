from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas import AuthResponse, LoginRequest, SignupRequest
from app.core.security import issue_token
from app.models.models import User, Workspace

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
def signup(req: SignupRequest, db: Session = Depends(get_db)) -> AuthResponse:
    existing = db.scalar(select(User).where(User.email == req.email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    workspace = Workspace(name=req.workspace_name)
    db.add(workspace)
    db.flush()
    user = User(workspace_id=workspace.id, email=req.email, name=req.name)
    db.add(user)
    db.commit()

    token = issue_token(user.id)
    return AuthResponse(
        access_token=token, user_id=user.id, workspace_id=workspace.id, name=user.name, email=user.email
    )


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """No password: this is an MVP demo. Email alone identifies the user,
    which is fine for local development but must not ship as-is."""
    user = db.scalar(select(User).where(User.email == req.email))
    if user is None:
        raise HTTPException(status_code=404, detail="No user with this email")

    token = issue_token(user.id)
    return AuthResponse(
        access_token=token, user_id=user.id, workspace_id=user.workspace_id, name=user.name, email=user.email
    )
