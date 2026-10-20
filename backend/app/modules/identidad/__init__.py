"""API pública del módulo identidad.

Regla: otros módulos SOLO pueden importar desde aquí.
"""

from app.modules.identidad.domain.entity import Role, User, UserStatus
from app.modules.identidad.domain.ports import (
    Clock,
    Hasher,
    TokenIssuer,
    UserRepository,
)

__all__ = [
    "User",
    "Role",
    "UserStatus",
    "UserRepository",
    "Hasher",
    "TokenIssuer",
    "Clock",
]