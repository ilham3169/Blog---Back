from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing import Annotated

from security import get_current_user
from jose import JWTError, jwt
from dotenv import dotenv_values
from database import SessionLocal

from models import Blogs, Users
from schemas import BlogCreate


import pytz

router = APIRouter(
    prefix="/blogs",
    tags=["blogs"]
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


TIMEZONE = pytz.timezone("Asia/Baku")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

db_dependency = Annotated[Session, Depends(get_db)]

def get_current_user(db: Session, token: str) -> Users:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")

    return user

@router.get("/all_blogs", status_code=status.HTTP_200_OK)
async def get_all_blogs(db: db_dependency, token: str = Depends(oauth2_scheme)):
    current_user = get_current_user(db, token)

    blogs = db.query(Blogs).filter(Blogs.author_id == current_user.id).order_by(Blogs.created_date.desc()).all()

    return [
        {
            "id": b.id,
            "title": b.title,
            "description": b.description,
            "created_date": b.created_date,
            "edit_date": b.edit_date,
            "author_id": b.author_id,
        }
        for b in blogs
    ]


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_blog_post(create_data: BlogCreate, db: db_dependency, token: str = Depends(oauth2_scheme)):
    current_user = get_current_user(db, token)
    title = create_data.title.strip()

    exist_blog = db.query(Blogs).filter(Blogs.title == title).first()

    if exist_blog and exist_blog.author_id == current_user.id:
        raise HTTPException(status_code=400, detail="This blog title exists")

    new_blog = Blogs(title=title, description=create_data.description.strip(),author_id=current_user.id)

    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)

    return {
        "message": "Blog created",
        "blog": {
            "id": new_blog.id,
            "title": new_blog.title,
            "description": new_blog.description,
            "author_id": new_blog.author_id,
            "created_date": new_blog.created_date,
            "edit_date": new_blog.edit_date,
        }
    }
