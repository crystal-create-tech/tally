from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.dependencies import get_current_user, require_role
from app.models import User, UserRole
from app.schemas import UserCreateRequest, UserResponse
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("",  response_model=UserResponse, status_code=201)
def create_user(
    create_request: UserCreateRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MANAGER)),
    db_session: Session = Depends(get_db_session),
):
    if current_user.role == UserRole.MANAGER and create_request.role != UserRole.EMPLOYEE:
        raise HTTPException(status_code=403, detail="Managers can only create employees")
    new_user = User(
        org_id=current_user.org_id,
        name=create_request.name,
        email=create_request.email,
        password_hash=hash_password(create_request.password),
        role=create_request.role,
        hourly_rate_cents=create_request.hourly_rate_cents,
    )
    db_session.add(new_user)
    try:
        db_session.commit()
    except IntegrityError:
        db_session.rollback()
        raise HTTPException(status_code=409, detail="Email is already registered")
    db_session.refresh(new_user)
    return new_user

