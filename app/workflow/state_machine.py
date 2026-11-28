from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CaseEvent, CaseSource, CaseStatus, ExceptionCase

ALLOWED_TRANSITIONS: dict[CaseStatus, set[CaseStatus]] = {
    CaseStatus.RECEIVED: {CaseStatus.ANALYZING},
    CaseStatus.ANALYZING: {CaseStatus.AWAITING_APPROVAL, CaseStatus.FAILED},
    CaseStatus.AWAITING_APPROVAL: {CaseStatus.APPROVED, CaseStatus.REJECTED},
    CaseStatus.APPROVED: {CaseStatus.EXECUTED, CaseStatus.FAILED},
    CaseStatus.FAILED: {CaseStatus.RECEIVED},
    CaseStatus.REJECTED: set(),
    CaseStatus.EXECUTED: set(),
}


class CaseNotFoundError(Exception):
    pass


class InvalidTransitionError(Exception):
    pass


def record_event(
    db_session: Session,
    exception_case: ExceptionCase,
    event_type: str,
    actor: str,
    payload: dict | None = None,
    from_status: CaseStatus | None = None,
    to_status: CaseStatus | None = None,
) -> None:
    db_session.add(
        CaseEvent(
            org_id=exception_case.org_id,
            case_id=exception_case.id,
            event_type=event_type,
            from_status=from_status.value if from_status else None,
            to_status=to_status.value if to_status else None,
            actor=actor,
            payload=payload or {},
        )
    )


def create_case(
    db_session: Session,
    org_id: int,
    description: str,
    source: CaseSource,
    actor: str,
    employee_id: int | None = None,
) -> ExceptionCase:
    new_case = ExceptionCase(
        org_id=org_id,
        employee_id=employee_id,
        source=source,
        description=description,
        status=CaseStatus.RECEIVED,
    )
    db_session.add(new_case)
    db_session.flush()
    record_event(db_session, new_case, "case_received", actor, to_status=CaseStatus.RECEIVED)
    return new_case


def lock_case(db_session: Session, case_id: int, org_id: int) -> ExceptionCase:
    locked_case = db_session.scalars(
        select(ExceptionCase)
        .where(ExceptionCase.id == case_id, ExceptionCase.org_id == org_id)
        .with_for_update()
    ).one_or_none()
    if locked_case is None:
        raise CaseNotFoundError(f"Case {case_id} not found")
    return locked_case


def transition_case(
    db_session: Session,
    exception_case: ExceptionCase,
    to_status: CaseStatus,
    actor: str,
    payload: dict | None = None,
) -> ExceptionCase:
    from_status = exception_case.status
    if to_status not in ALLOWED_TRANSITIONS[from_status]:
        raise InvalidTransitionError(
            f"Cannot move case {exception_case.id} from {from_status.value} to {to_status.value}"
        )
    exception_case.status = to_status
    record_event(
        db_session,
        exception_case,
        "status_changed",
        actor,
        payload,
        from_status=from_status,
        to_status=to_status,
    )
    return exception_case