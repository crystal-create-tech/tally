from sqlalchemy.orm import Session

from app.models import CaseStatus, ExceptionCase
from app.workflow.state_machine import record_event, transition_case


def run_stub_analysis(db_session: Session, exception_case: ExceptionCase) -> ExceptionCase:
    transition_case(db_session, exception_case, CaseStatus.ANALYZING, actor="system")
    exception_case.proposed_adjustment = {
        "action": "manual_review",
        "reason": "Stub analyzer: no automatic adjustment proposed",
    }
    record_event(
        db_session,
        exception_case,
        "analysis_completed",
        actor="stub_analyzer",
        payload=exception_case.proposed_adjustment,
    )
    return transition_case(db_session, exception_case, CaseStatus.AWAITING_APPROVAL, actor="system")