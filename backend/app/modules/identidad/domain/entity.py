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
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def is_blocked(self, ahora: datetime | None = None) -> bool:
        if self.status == UserStatus.BLOCKED and self.locked_until:
            ahora = ahora or datetime.now(timezone.utc)
            return self.locked_until > ahora
        return False