from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.modules.identidad.domain.entity import User

class UserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> User | None:
        ...

    async def get_by_phone(self, phone: str) -> User | None:
        ...

    async def save(self, user: User) -> User:
        ...

class Hasher(Protocol):
    def generate_hash(self, value: str) -> str:
        ...

    def verify_hash(self, value: str, hash_storage: str) -> bool:
        ...

class TokenIssuer(Protocol):
    def issue_access_token(self, user_id: UUID, role: str) -> str:
        ...

    def decode_access_token(self, token: str) -> dict:
        ...

class Clock(Protocol):
    def now(self) -> datetime:
        ...

class GeneradorRefresh(Protocol):
    def generar(self) -> str:
        """Devuelve un refresh token nuevo, aleatorio y de un solo uso."""
        ...

    def hashear(self, token: str) -> str:
        """Devuelve el hash que se guarda en la base. El token en claro nunca se guarda."""
        ...
