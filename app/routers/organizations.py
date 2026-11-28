from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models import Organization, User, UserRole
from app.schemas import OrganizationSignupRequest, TokenResponse
from app.security import create_access_token, hash_password

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.post("/signup", response_model=TokenResponse, status_code=201)
def sign_up_organization(
    signup_request: OrganizationSignupRequest,
    db_session: Session = Depends(get_db_session),
):
    new_organization = Organization(
        name=signup_request.organization_name,
        timezone=signup_request.timezone,
    )
    admin_user = User(
        name=signup_request.admin_name,
        email=signup_request.admin_email,
        password_hash=hash_password(signup_request.admin_password),
        role=UserRole.ADMIN,
    )
    db_session.add(new_organization)
    db_session.flush()
    admin_user.org_id = new_organization.id
    db_session.add(admin_user)
    try:
        db_session.commit()
    except IntegrityError:
        db_session.rollback()
        raise HTTPException(status_code=409, detail="Email is already registered")
    return TokenResponse(access_token=create_access_token(admin_user.id))