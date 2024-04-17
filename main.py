import os
from datetime import datetime
from hashlib import sha512
from typing import Optional, Annotated

from fastapi import FastAPI, Depends, HTTPException, Cookie
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse, JSONResponse, Response

from crud import insert_alarm, init_tables, get_alarm_with_conditions, clear_alarms, delete_alarms, user_login, \
    get_user_by_id
from data_schema import AlarmBase
from data_schema.user import UserBase, UserSchema
from date_orm import SessionLocal

init_tables()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

login_user_cache = {}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def token_check(token: Annotated[str | None, Cookie()] = None) -> bool:
    if token is None:
        return False
    uid = login_user_cache.get(token, None)
    if uid is None:
        return False
    return True


@app.post("/alarm/")
async def add_alarm(alarm: AlarmBase, db: Session = Depends(get_db)):
    try:
        insert_alarm(db, alarm)
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error occurreds")
    return {"state": "ok"}


@app.get("/alarm/")
async def get_alarm(
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        min_temp: Optional[float] = None,
        max_temp: Optional[float] = None,
        smoke_det: Optional[bool] = None,
        fire_det: Optional[bool] = None,
        cleared: Optional[bool] = None,
        db: Session = Depends(get_db),
        token_result=Depends(token_check)
):
    if not token_result:
        return RedirectResponse("/login")
    try:
        items = get_alarm_with_conditions(
            db,
            start_time,
            end_time,
            min_temp,
            max_temp,
            smoke_det,
            fire_det,
            cleared
        )
        return {
            "state": "ok",
            "alarms": items
        }
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error occurred")


@app.delete("/alarm/")
async def delete_alarm_by_ids(alarm_ids: list[int], db: Session = Depends(get_db), token_result=Depends(token_check)):
    if not token_result:
        return RedirectResponse("/login")
    try:
        delete_alarms(db, alarm_ids)
        return {"state": "ok"}
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error occurred")


@app.post("/alarm/clear/")
async def set_alarm_cleared(alarm_ids: list[int], db: Session = Depends(get_db), token_result=Depends(token_check)):
    if not token_result:
        return RedirectResponse("/login")
    try:
        clear_alarms(db, alarm_ids)
        return {"state": "ok"}
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error occurred")


app.mount("/assets", StaticFiles(directory="./static/assets"), name="assets")


@app.get("/")
async def get_index(token_result=Depends(token_check)):
    if not token_result:
        return RedirectResponse("/login")
    with open("static/index.html", 'rt') as f:
        index = f.read()
    return HTMLResponse(index)


@app.get("/favicon.ico")
async def get_favicon():
    with open("static/favicon.ico", 'rb') as f:
        ico = f.read()
    return Response(ico, media_type="image/x-icon")


@app.get("/login")
async def login_html(token_result=Depends(token_check)):
    if token_result:
        return RedirectResponse("/")
    with open("static/login/index.html", 'r') as f:
        ico = f.read()
    return HTMLResponse(ico)


@app.post("/login")
async def login(user: UserBase, db: Session = Depends(get_db)):
    ret, data = user_login(db, user.name, user.hash_pwd)
    if ret:
        resp = JSONResponse({
            "code": 0,
            "status": "ok"
        })
        token = sha512(f"{user.name}_{user.hash_pwd}_{datetime.now().timestamp()}".encode()).hexdigest().lower()
        resp.set_cookie("token", value=token)
        login_user_cache[token] = int(data)
    else:
        resp = JSONResponse({
            "code": -1,
            "status": str(data)
        }, status_code=200)
    return resp


@app.get("/user_info/", response_model=UserSchema)
async def get_user_info(token: Annotated[str | None, Cookie()] = None, db: Session = Depends(get_db)):
    if token is None:
        return RedirectResponse("/login")
    uid = login_user_cache.get(token, None)
    if uid is None:
        return RedirectResponse("/login")
    user = get_user_by_id(db, uid)
    return user


@app.get("/logout")
async def get_user_info(token: Annotated[str | None, Cookie()] = None):
    _ = login_user_cache.pop(token, None)
    return RedirectResponse("/login")
