from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

from app.modules.identidad.domain.entity import Role, UserStatus
from app.modules.identidad.domain.errors import InvalidPhone
from app.modules.identidad.domain.values import Phone


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


class LogoutRequest(BaseModel):
    refresh_token: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Refresh token de la sesión que se quiere cerrar.",
    )


class HealthResponse(BaseModel):
    estado: str = "ok"


Text80 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]

class RegisterRequest(BaseModel):
    full_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=120)]
    phone: str = Field(..., description="Celular colombiano móvil, con o sin +57.")
    email: EmailStr | None = None
    password: str = Field(..., min_length=8, max_length=128)
    municipality: Text80 = "Neiva"
    district: Text80 | None = None
    accepts_policy: bool
    policy_version: str = Field(..., min_length=1, max_length=20)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "Ernesto Ramírez",
                "phone": "300 123 4567",
                "email": None,
                "password": "MiFinca2026",
                "municipality": "Neiva",
                "district": "Fortalecillas",
                "accepts_policy": True,
                "policy_version": "2026.1",
            }
        }
    )

    @field_validator("email", "district", mode="before")
    @classmethod
    def _blank_to_none(cls, v):
        return None if isinstance(v, str) and not v.strip() else v

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        try:
            return Phone.desde_entrada(v, solo_movil=True).value
        except InvalidPhone as exc:
            raise ValueError("El celular no es un número móvil colombiano válido.") from exc

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        if not (any(c.isalpha() for c in v) and any(c.isdigit() for c in v)):
            raise ValueError("La contraseña debe tener al menos una letra y un número.")
        return v

class RegisteredUser(BaseModel):
    id: UUID
    full_name: str | None
    phone: str
    role: Role
    municipality: str | None
    district: str | None


class RegisterTokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Segundos de vida del access token.")


class RegisterResponse(BaseModel):
    user: RegisteredUser
    tokens: RegisterTokens