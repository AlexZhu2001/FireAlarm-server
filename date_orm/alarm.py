from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, DateTime, Float

from .database import Base


class AlarmOrm(Base):
    __tablename__ = 'alarms'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    temperature = Column(Float)
    smoke_detected = Column(Boolean)
    fire_detected = Column(Boolean)
    cleared = Column(Boolean, default=False)
