import enum

from pydantic import BaseModel


class UserPrivilege(enum.IntEnum):
    admin = 0
    user = 1


class UserBase(BaseModel):
    name: str
    hash_pwd: str


class UserSchema(UserBase):
    id: int
    privilege: UserPrivilege

    class Config:
        from_attributes = True
