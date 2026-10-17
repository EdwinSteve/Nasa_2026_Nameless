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
    celular: str = Field(
        ...,
        examples=["3001234567"],
        description="Celular colombiano. Se acepta con o sin prefijo +57.",
    )
    contrasena: str = Field(..., min_length=1, max_length=128, examples=["MiFinca2026"])

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"celular": "3001234567", "contrasena": "MiFinca2026"},
        }
    )


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT firmado. Caduca en 15 minutos.")
    refresh_token: str = Field(
        ...,
        description="Token opaco de 30 días. Se devuelve una sola vez y cada uso lo reemplaza.",
    )
    token_type: str = Field(default="bearer")
    expira_en: int = Field(..., description="Segundos de vida del access token.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2ZjFj...",
                "refresh_token": "Xk2rQ8s0uYwPqN3bZ1cV7mHjL4tA9dFgE6kR2oWzIyU",
                "token_type": "bearer",
                "expira_en": 900,
            }
        }
    )


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, max_length=255, examples=["Xk2rQ8s0uYwPqN3bZ1cV7m"])


class HealthResponse(BaseModel):
    estado: str = "ok"