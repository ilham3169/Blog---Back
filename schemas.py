from optparse import Option
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# <-- User --> #
class LoginRequest(BaseModel):
    username: str
    # password_hash: str = Field(min_length=6, max_length=72)
    password_hash: str

class UserCreate(BaseModel):
    username: str
    email: str
    password_hash: str


# <-- Blog --> #
class BlogCreate(BaseModel):
    title: str
    description: str








