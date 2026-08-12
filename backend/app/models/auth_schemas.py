"""API-facing auth request/response schemas"""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    role: str = "owner"
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
