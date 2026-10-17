from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.modules.identidad.domain.entity import Sesion, User

class UserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> User | None:
        ...

    async def get_by_phone(self, phone: str) -> User | None:
        ...

    async def save(self, user: User) -> User:
        ...

class SesionRepository(Protocol):
    async def crear(self, sesion: Sesion) -> None:
        ...

    async def buscar_por_hash(self, token_hash: str) -> Sesion | None:
        ...

    async def buscar_por_hash_para_actualizar(self, token_hash: str) -> Sesion | None:
        """Igual que buscar_por_hash, pero bloquea la fila hasta el fin de la transacción
        (SELECT ... FOR UPDATE). Evita que dos /refresh simultáneos canjeen el mismo token."""
        ...

    async def marcar_usada(self, sesion_id: UUID, reemplazada_por: UUID, ahora: datetime) -> None:
        ...

    async def revocar(self, sesion_id: UUID, ahora: datetime) -> None:
        ...

    async def revocar_familia(self, family_id: UUID, ahora: datetime) -> None:
        ...

    async def revocar_todas_del_usuario(self, user_id: UUID, ahora: datetime) -> None:
        ...

class EventoRepository(Protocol):
    async def registrar(self, evento: str, user_id: UUID | None, meta: dict | None = None) -> None:
        ...

class UnitOfWork(Protocol):
    async def confirmar(self) -> None:
        """Hace commit de todos los cambios de la operación actual."""
        ...

class Hasher(Protocol):
    def generate_hash(self, value: str) -> str:
        ...

    def verify_hash(self, value: str, hash_storage: str) -> bool:
        ...

    def necesita_rehash(self, hash_storage: str) -> bool:
        ...

class TokenIssuer(Protocol):
    duracion_segundos: int

    def issue_access_token(self, user_id: UUID, rol: str) -> str:
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
