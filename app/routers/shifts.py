from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.dependencies import get_current_user
from app.models import Shift, User
from app.schemas import ClockInRequest, ShiftResponse

router = APIRouter(prefix="/shifts", tags=["shifts"])

@router.post("/clock-in", response_model=ShiftResponse, status_code=201)
def clock_in(
    request_body: ClockInRequest,
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
):
    new_shift = Shift(
        org_id=current_user.org_id,
        user_id=current_user.id,
        clock_in_at=func.now(),
        source=request_body.source,
    )
    db_session.add(new_shift)
    try:
        db_session.commit()
    except IntegrityError as error:
        db_session.rollback()
        if"one_open_shift_per_user" in str(error.orig):
            raise HTTPException(status_code=409, detail="User already has an open shift")
        raise
    db_session.refresh(new_shift)
    return new_shift


@router.post("/clock-out", response_model=ShiftResponse)
def clock_out(
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
):
    close_open_shift = (
        update(Shift)
        .where(Shift.user_id == current_user.id, Shift.clock_out_at.is_(None))
        .values(clock_out_at=func.now())
        .returning(Shift)
    )
    closed_shift = db_session.scalars(close_open_shift).one_or_none()
    if closed_shift is None:
        raise HTTPException(status_code=409, detail="User has no open shift")
    db_session.commit()
    return closed_shift
