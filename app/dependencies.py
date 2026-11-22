from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models import User


def get_current_user(
        x_user_id: int = Header(),
        db_session: Session = Depends(get_db_session),
) -> User:
    current_user = db_session.get(User, x_user_id)
    if current_user is None:
        raise HTTPException(status_code=401, detail="Unknown user")
    return current_user

