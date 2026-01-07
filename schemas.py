from optparse import Option
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    username: str
    password_hash: str

class LoginCreate(BaseModel):
    username: str
    password_hash: str
    role_id: int

class LoginEdit(BaseModel):
    username: Optional[str] = None 
    password_hash: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = True




