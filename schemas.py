from optparse import Option
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    username: str
    password_hash: str

class UserCreate(BaseModel):
    username: str
    email: str
    password_hash: str





