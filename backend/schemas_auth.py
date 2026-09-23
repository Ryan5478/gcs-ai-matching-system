from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: Literal["candidate", "employer", "admin"]


class UserRead(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    email: str
    full_name: str
