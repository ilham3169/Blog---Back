import bcrypt
from datetime import datetime, timedelta, timezone
from dotenv import dotenv_values
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Annotated, Optional
from fastapi import  Depends, HTTPException
from fastapi.security import  OAuth2PasswordBearer
from jose.exceptions import ExpiredSignatureError
from database import  db_dependency
from models import Users

env = dotenv_values(".env")

SECRET_KEY = env["SECRET_KEY"]
ALGORITHM = env["ALGORITHM"]

if not SECRET_KEY: raise RuntimeError("SECRET_KEY is missing in .env")
if not ALGORITHM: raise RuntimeError("ALGORITHM is missing in .env")

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30  
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")



def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())

def create_token(*, subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = _now_ts()
    payload = {
        "sub": subject,
        "type": token_type,     
        "iat": now,
        "exp": now + int(expires_delta.total_seconds()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)    

def create_access_token(username: str) -> str:
    return create_token(
        subject=username,
        token_type="access",
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

def create_refresh_token(username: str) -> str:
    return create_token(
        subject=username,
        token_type="refresh",
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def authenticate_user(db: Session, username: str, password: str) -> Optional[Users]:
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: db_dependency,) -> Users:
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")

        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if hasattr(user, "is_active") and not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    return user