from dataclasses import dataclass

from app.modules.identidad.domain.entity import User


@dataclass(frozen=True)
class ParTokens:
    """Resultado de un login o de un refresh: un access token y su refresh token nuevo."""

    access_token: str
    refresh_token: str
    expira_en: int
    token_type: str = "bearer"

@dataclass(frozen=True)
class DatosRegistro:
    full_name: str
    phone: str
    email: str | None
    password: str
    municipality: str
    district: str | None
    accepts_policy: bool
    policy_version: str


@dataclass(frozen=True)
class ResultadoRegistro:
    usuario: User
    tokens: ParTokens
