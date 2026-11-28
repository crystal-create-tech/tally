import datetime
import enum

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    ADMIN = "admin"

class ShiftSource(str, enum.Enum):
    MOBILE = "mobile"
    KIOSK = "kiosk"
    WEB = "web"

class CaseStatus(str, enum.Enum):
    RECEIVED = "received"
    ANALYZING = "analyzing"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"

class CaseSource(str, enum.Enum):
    MANUAL = "manual"
    EMAIL = "email"
    WEBHOOK = "webhook"

def enum_column_type(enum_class: type[enum.Enum], type_name: str) -> Enum:
    return Enum(
        enum_class,
        name=type_name,
        values_callable=lambda enum_members: [member.value for member in enum_members],
    )

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    timezone: Mapped[str] = mapped_column(String(64), default="America/Los_Angeles")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda role_enum: [role.value for role in role_enum]),
        default=UserRole.EMPLOYEE,
    )
    password_hash: Mapped[str] = mapped_column(String(255))
    hourly_rate_cents: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

class Shift(Base):
    __tablename__= "shifts"
    __table_args__ = (
        Index(
            "one_open_shift_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("clock_out_at IS NULL"),
        ),
        CheckConstraint(
            "clock_out_at IS NULL OR clock_out_at > clock_in_at",
            name="clock_out_after_clock_in",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    clock_in_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    clock_out_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    source:  Mapped[ShiftSource] = mapped_column(
        Enum(ShiftSource, name="shift_source", values_callable=lambda source_enum: [source.value for source in source_enum]),
        default=ShiftSource.MOBILE,
    )
    created_at:  Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

class ExceptionCase(Base):
    __tablename__ = "exception_cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    source: Mapped[CaseSource] = mapped_column(enum_column_type(CaseSource, "case_source"))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[CaseStatus] = mapped_column(
        enum_column_type(CaseStatus, "case_status"),
        default=CaseStatus.RECEIVED,
        index=True,
    )
    proposed_adjustment: Mapped[dict | None] = mapped_column(JSONB)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    events: Mapped[list["CaseEvent"]] = relationship(order_by="CaseEvent.id")


class CaseEvent(Base):
    __tablename__ = "case_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("exception_cases.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    from_status: Mapped[str | None] = mapped_column(String(30))
    to_status: Mapped[str | None] = mapped_column(String(30))
    actor: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )