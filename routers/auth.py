from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing import Annotated

from security import hash_password, verify_password
from models import Users
from schemas import LoginRequest, LoginCreate, LoginEdit
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from dotenv import dotenv_values
from database import SessionLocal

import pytz

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

env = dotenv_values(".env")

SECRET_KEY = env["SECRET_KEY"]
ALGORITHM = env["ALGORITHM"]

ACCESS_TOKEN_EXPIRE_MINUTES = 15
TIMEZONE = pytz.timezone("Asia/Baku")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

db_dependency = Annotated[Session, Depends(get_db)]


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not pwd_context.verify(password, user.password_hash):
        return False 
    return user


@router.post("/token")
async def login_for_access_token(db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/verify-token")
async def verify_token(token: str, db: db_dependency):
    try:
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = payload.get("exp")
        username: str = payload.get("sub")
        current_timestamp = datetime.now(timezone.utc).timestamp()
        seconds_left = exp_timestamp - current_timestamp


        user = db.query(Users).filter(Users.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "status": "valid",
            "user": {
                "id": user.id,
                "username": user.username,
                "fullname": user.fullname,
            },
            "time": seconds_left
        }

    except jwt.ExpiredSignatureError:
        return {"status": "expired", "message": "token expired"}
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/login", status_code=status.HTTP_200_OK)
async def check_login(credentials: LoginRequest, db: db_dependency):
    user = db.query(Users).filter(Users.username == credentials.username).first()

    if not user or not verify_password(credentials.password_hash, user.password_hash): 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    
    if not user.is_active: 
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    token = create_access_token(data={"sub": user.username})
    return {"message": "Successful login", "username": user.username, "access_token": token}

@router.patch("/last_login/{username}", status_code=status.HTTP_200_OK)
async def update_last_login(username: str, db: db_dependency):
    user = db.query(Users).filter(Users.username == username).first()
    if not user: 
        raise HTTPException(status_code=404, detail="User not found")

    user.last_login = datetime.now(TIMEZONE)
    db.commit()
    db.refresh(user)

    return {"message" : "Successful", "user" : user}