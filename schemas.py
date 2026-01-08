from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    # password_hash: str = Field(min_length=6, max_length=72)
    password_hash: str

class UserCreate(BaseModel):
    username: str
    email: str
    password_hash: str

class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

    current_password: Optional[str] = None
    new_password: Optional[str] = None


class BlogCreate(BaseModel):
    title: str
    description: str

class BlogUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None







