from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from app.modules.identidad.domain.values import Email, Phone


class Role(str, Enum):
    APRENDIZ = "aprendiz"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"


class UserStatus(str, Enum):
    ACTIVE = "activo"
    INACTIVE = "inactivo"
    BLOCKED = "bloqueado"
    PENDING = "pendiente"


@dataclass
class User:
    phone: Phone
    email: Email
    password_hash: str
    role: Role = Role.APRENDIZ
    status: UserStatus = UserStatus.PENDING
    id: UUID = field(default_factory=uuid4)
    failed_attempts: int = 0
    locked_until: datetime | None = None
    last_login_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def is_blocked(self, ahora: datetime | None = None) -> bool:
        """La cuenta está bloqueada mientras `locked_until` esté en el futuro.

        El bloqueo se decide solo por la fecha de desbloqueo: cuando esa fecha pasa,
        la cuenta vuelve a estar disponible sin tocar el estado de la cuenta.
        """
        if self.locked_until is None:
            return False
        ahora = ahora or datetime.now(timezone.utc)
        return self.locked_until > ahora


@dataclass
class Sesion:
    """Refresh token guardado por hash. Cada login crea una familia nueva; cada
    refresh crea un token de la misma familia y marca el anterior como usado."""

    user_id: UUID
    token_hash: str
    family_id: UUID
    expires_at: datetime
    id: UUID = field(default_factory=uuid4)
    used_at: datetime | None = None
    replaced_by: UUID | None = None
    revoked_at: datetime | None = None
    created_at: datetime | None = None

    @property
    def usada(self) -> bool:
        return self.used_at is not None

    @property
    def revocada(self) -> bool:
        return self.revoked_at is not None

    def expirada(self, ahora: datetime) -> bool:
        return self.expires_at <= ahora
