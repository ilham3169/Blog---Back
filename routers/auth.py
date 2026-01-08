from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Annotated
from jose.exceptions import ExpiredSignatureError
from models import Users
from schemas import LoginRequest, UserCreate, UserUpdateRequest
from datetime import datetime
from jose import JWTError
from dotenv import dotenv_values
from database import db_dependency
from email_service import send_welcome_email, send_login_message
from security import hash_password, get_current_user, authenticate_user, create_access_token, create_refresh_token, decode_token, _now_ts, verify_password


import pytz

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


env = dotenv_values(".env")
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30  
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

TIMEZONE = pytz.timezone("Asia/Baku")


@router.get("/me")
async def me(current_user: Annotated[Users, Depends(get_current_user)]):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "is_active": getattr(current_user, "is_active", True),
    }

@router.patch("/update_me", status_code=status.HTTP_200_OK)
def update_me(payload: UserUpdateRequest, db: db_dependency ,current_user: Users = Depends(get_current_user)):
    if payload.username is not None:
        exists = db.query(Users).filter(Users.username == payload.username, Users.id != current_user.id).first()
        if exists: raise HTTPException(status_code=400, detail="This username already exists")
        current_user.username = payload.username

    if payload.email is not None:
        exists = db.query(Users).filter(Users.email == payload.email, Users.id != current_user.id).first()
        if exists: raise HTTPException(status_code=400, detail="This email already exists")
        current_user.email = payload.email

    if payload.new_password is not None:
        if not payload.current_password:
            raise HTTPException(status_code=400,detail="current_password is required to change password")

        if not verify_password(payload.current_password, current_user.password_hash):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        current_user.password_hash = hash_password(payload.new_password)

    if (payload.username is None and payload.email is None and payload.new_password is None): 
        raise HTTPException(status_code=400, detail="No fields to update")

    db.commit()
    db.refresh(current_user)

    return {
        "message": "User updated successfully",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": getattr(current_user, "email", None),
        },
    }

@router.post("/token")
async def login_for_access_token(db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()], background_tasks: BackgroundTasks):
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials", headers={"WWW-Authenticate": "Bearer"})

    if hasattr(user, "is_active") and not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    access_token = create_access_token(user.username)
    refresh_token = create_refresh_token(user.username)

    background_tasks.add_task(send_login_message, user.email, user.username)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token, 
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {"id": user.id, "username": user.username},
    }

@router.post("/refresh")
async def refresh_access_token(db: db_dependency, refresh_token: str):
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if hasattr(user, "is_active") and not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    new_access = create_access_token(user.username)
    return {"access_token": new_access, "token_type": "bearer", "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60}


@router.get("/verify-token")
async def verify_token(token: Annotated[str, Depends(oauth2_scheme)],db: db_dependency):
    user = get_current_user(token, db)

    payload = decode_token(token)
    seconds_left = int(payload["exp"]) - _now_ts()

    return {
        "status": "valid",
        "user": {"id": user.id, "username": user.username},
        "time_left_seconds": max(seconds_left, 0),
    }


@router.post("/login")
async def login_json(db: db_dependency, body: LoginRequest):
    user = authenticate_user(db, body.username, body.password_hash)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(user.username)
    refresh_token = create_refresh_token(user.username)


    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.patch("/last_login/{username}", status_code=status.HTTP_200_OK)
async def update_last_login(username: str, db: db_dependency):
    user = db.query(Users).filter(Users.username == username).first()
    if not user: 
        raise HTTPException(status_code=404, detail="User not found")

    user.last_login = datetime.now(TIMEZONE)
    db.commit()
    db.refresh(user)

    return {"message" : "Successful", "user" : user}

@router.post("/register", status_code=status.HTTP_200_OK)
async def register_user(credentials: UserCreate, db: db_dependency, background_tasks: BackgroundTasks):
    user_exists = db.query(Users).filter(Users.username == credentials.username).first()
    if user_exists: 
        raise HTTPException(status_code=400, detail="This username exists")

    email_exists = db.query(Users).filter(Users.email == credentials.email).first()
    if email_exists: 
        raise HTTPException(status_code=400, detail="This email exists")
    
    user_data = credentials.dict()
    user_data["password_hash"] = hash_password(user_data["password_hash"])
    
    new_user = Users(**user_data)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    background_tasks.add_task(send_welcome_email, new_user.email, new_user.username)
    return {"message" : "Successful", "user" : new_user}

