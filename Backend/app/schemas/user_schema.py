from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import re

class UserCreate(BaseModel):
    role_id: int
    name: str
    last_name: str
    email: EmailStr
    password: str

    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not re.search(r"[A-Z]", v):
            raise ValueError('La contraseña debe tener al menos una letra mayúscula')
        if not re.search(r"[a-z]", v):
            raise ValueError('La contraseña debe tener al menos una letra minúscula')
        if not re.search(r"\d", v):
            raise ValueError('La contraseña debe tener al menos un número')
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError('La contraseña debe tener al menos un carácter especial')
        return v


# =========================
# UPDATE
# =========================

class UserUpdate(BaseModel):
    role_id: Optional[int] = None
    name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator('password')
    def validate_password(cls, v):
        if v is None or v == '':
            return v
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not re.search(r"[A-Z]", v):
            raise ValueError('La contraseña debe tener al menos una letra mayúscula')
        if not re.search(r"[a-z]", v):
            raise ValueError('La contraseña debe tener al menos una letra minúscula')
        if not re.search(r"\d", v):
            raise ValueError('La contraseña debe tener al menos un número')
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError('La contraseña debe tener al menos un carácter especial')
        return v


# =========================
# RESPONSE
# =========================

class UserResponse(BaseModel):
    id: int
    role_id: int
    role_name: Optional[str] = None
    name: str
    last_name: str
    email: EmailStr
    is_active: bool
    created_at: Optional[datetime]
    telegram_chat_id: Optional[str] = None

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class SocialLoginRequest(BaseModel):
    id_token: str


class TelegramLinkRequest(BaseModel):
    user_id: int
    telegram_chat_id: str