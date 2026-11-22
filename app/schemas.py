import datetime

from pydantic import BaseModel, ConfigDict

from app.models import ShiftSource

class ClockInRequest(BaseModel):
    source: ShiftSource = ShiftSource.MOBILE


class ShiftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    clock_in_at: datetime.datetime
    clock_out_at: datetime.datetime | None
    source: ShiftSource


