from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.identidad.domain.entity import Role, UserStatus


class UserBase(BaseModel):
    phone: str = Field(..., examples=["+573001234567"])
    email: EmailStr
    role: Role = Role.APRENDIZ


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: UserStatus
    created_at: datetime | None = None


class LoginRequest(BaseModel):
    phone: str = Field(..., examples=["+573001234567"])
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class HealthResponse(BaseModel):
    estado: str = "ok"