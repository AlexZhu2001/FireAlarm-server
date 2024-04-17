from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, Text

from .database import Base


class UserOrm(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, nullable=False)
    hash_pwd = Column(Text, nullable=False)
    privilege = Column(Integer, nullable=False)
    name = Column(Text, nullable=False, unique=True)
