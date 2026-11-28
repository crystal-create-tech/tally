import datetime
import zoneinfo

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import ShiftSource, UserRole

class ClockInRequest(BaseModel):
    source: ShiftSource = ShiftSource.MOBILE


class ShiftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    clock_in_at: datetime.datetime
    clock_out_at: datetime.datetime | None
    source: ShiftSource


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OrganizationSignupRequest(BaseModel):
    organization_name: str = Field(min_length=1, max_length=200)
    timezone: str = "America/Los_Angeles"
    admin_name: str = Field(min_length=1, max_length=200)
    admin_email: EmailStr
    admin_password: str = Field(min_length=8)


    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, timezone_name: str) -> str:
        if timezone_name not in zoneinfo.available_timezones():
            raise ValueError(f"Unknown timezone: {timezone_name}")
        return timezone_name


class UserCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRole = UserRole.EMPLOYEE
    hourly_rate_cents: int = Field(default=0, ge=0)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    org_id: int
    email: str
    name: str
    role: UserRole
    hourly_rate_cents: int

    