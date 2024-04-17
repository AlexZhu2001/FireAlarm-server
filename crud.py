from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from data_schema import AlarmBase
from data_schema.user import UserPrivilege
from date_orm import AlarmOrm, engine, Base, SessionLocal
from date_orm.user import UserOrm
from hashlib import sha512


def get_alarm(db: Session, alarm_id: int):
    return db.query(AlarmOrm).filter(AlarmOrm.id == alarm_id).first()


def get_alarm_with_conditions(db: Session,
                              start_time: Optional[datetime] = None,
                              end_time: Optional[datetime] = None,
                              min_temp: Optional[float] = None,
                              max_temp: Optional[float] = None,
                              smoke_det: Optional[bool] = None,
                              fire_det: Optional[bool] = None,
                              cleared: Optional[bool] = None):
    conds = [
        AlarmOrm.timestamp >= start_time if start_time is not None else None,
        AlarmOrm.timestamp <= end_time if end_time is not None else None,
        AlarmOrm.temperature >= min_temp if min_temp is not None else None,
        AlarmOrm.temperature <= max_temp if max_temp is not None else None,
        AlarmOrm.fire_detected == fire_det if fire_det is not None else None,
        AlarmOrm.smoke_detected == smoke_det if smoke_det is not None else None,
        AlarmOrm.cleared == cleared if cleared is not None else None
    ]

    conds = list(filter(lambda x: x is not None, conds))

    if not conds:
        return db.query(AlarmOrm).all()
    else:
        return db.query(AlarmOrm).filter(*conds).all()


def get_all_alarm(db: Session):
    return db.query(AlarmOrm).all()


def insert_alarm(db: Session, alarm: AlarmBase):
    db_alarm = AlarmOrm(
        timestamp=alarm.timestamp,
        temperature=alarm.temperature,
        smoke_detected=alarm.smoke_detected,
        fire_detected=alarm.fire_detected,
    )
    db.add(db_alarm)
    db.commit()
    db.refresh(db_alarm)
    return db_alarm


def delete_alarms(db: Session, alarm_ids: list[int]):
    item = db.query(AlarmOrm).filter(AlarmOrm.id.in_(alarm_ids))
    item.delete()
    db.commit()


def clear_alarms(db: Session, alarm_ids: list[int]):
    items = db.query(AlarmOrm).filter(AlarmOrm.id.in_(alarm_ids))
    items.update({AlarmOrm.cleared: True})
    db.commit()


def create_user(db: Session, username: str, hash_pwd: str) -> (bool, str):
    if db.query(UserOrm).filter(UserOrm.name == username).count() != 0:
        return False, "User already exists!"
    user = UserOrm(
        name=username,
        privilege=UserPrivilege.user,
        hash_pwd=hash_pwd
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return True, ""


def delete_user(db: Session, uid: int):
    user = db.query(UserOrm).filter(UserOrm.id == uid).first()
    db.delete(user)
    db.commit()


def user_login(db: Session, name: str, hash_pwd: str) -> (bool, str | int):
    user = db.query(UserOrm).filter(UserOrm.name == name).first()
    if user is None:
        return False, "The user does not exist!"
    ret = user.hash_pwd == hash_pwd
    return ret, user.id if ret else "Password is incorrect!"


def set_user_privilege(db: Session, uid: int, priv: UserPrivilege):
    user = db.query(UserOrm).filter(UserOrm.id == uid)
    if user is None:
        return
    user.update({UserOrm.privilege: priv})
    db.commit()


def get_user_privilege(db: Session, uid: int) -> UserPrivilege | None:
    user = db.query(UserOrm).filter(UserOrm.id == uid).first()
    if user is None:
        return None
    return user.privilege


def get_users(db: Session):
    return db.query(UserOrm).all()


def get_user_by_id(db: Session, uid: int):
    return db.query(UserOrm).filter(UserOrm.id == uid).first()


def get_user_by_name(db: Session, name: str):
    return db.query(UserOrm).filter(UserOrm.name == name).first()


def init_tables():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(UserOrm).count() == 0:
        create_user(db, "admin", hash_pwd=sha512("admin".encode()).hexdigest().lower())
        user = get_user_by_name(db, "admin")
        set_user_privilege(db, user.id, UserPrivilege.admin)
