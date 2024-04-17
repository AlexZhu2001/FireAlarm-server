from datetime import datetime

from pydantic import BaseModel


class AlarmBase(BaseModel):
    timestamp: datetime
    temperature: float
    smoke_detected: bool
    fire_detected: bool


class AlarmSchema(AlarmBase):
    id: int
    cleared: bool = False

    class Config:
        from_attributes = True
