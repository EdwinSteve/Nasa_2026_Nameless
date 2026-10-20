"""Dobles de prueba en memoria para los puertos de identidad.

Implementan los mismos Protocol que los adaptadores reales, así que los casos de uso
se prueban sin base de datos ni hashing lento.
"""

from datetime import datetime, timedelta
from uuid import UUID

from app.modules.identidad.domain.entity import Sesion


class RelojFalso:
    def __init__(self, ahora: datetime) -> None:
        self._ahora = ahora

    def now(self) -> datetime:
        return self._ahora

    def avanzar(self, **kwargs) -> None:
        self._ahora += timedelta(**kwargs)


class HasherFalso:
    """Hash reversible y predecible: 'hash:<valor>'. Permite forzar necesita_rehash."""

    def __init__(self, necesita_rehash: bool = False) -> None:
        self._necesita_rehash = necesita_rehash

    def generate_hash(self, value: str) -> str:
        return f"hash:{value}"

    def verify_hash(self, value: str, hash_storage: str) -> bool:
        return hash_storage == f"hash:{value}"

    def necesita_rehash(self, hash_storage: str) -> bool:
        return self._necesita_rehash


class TokensFalsos:
    duracion_segundos = 900

    def issue_access_token(self, user_id: UUID, rol: str) -> str:
        return f"access:{user_id}:{rol}"

    def decode_access_token(self, token: str) -> dict:
        raise NotImplementedError


class GeneradorFalso:
    def __init__(self) -> None:
        self._n = 0

    def generar(self) -> str:
        self._n += 1
        return f"refresh-{self._n}"

    def hashear(self, token: str) -> str:
        return f"h({token})"


class UsuariosFalsos:
    def __init__(self) -> None:
        self.por_id: dict = {}

    def agregar(self, usuario) -> None:
        self.por_id[usuario.id] = usuario

    async def get_by_id(self, user_id: UUID):
        return self.por_id.get(user_id)

    async def get_by_phone(self, phone: str):
        return next((u for u in self.por_id.values() if u.phone.value == phone), None)

    async def get_by_email(self, email: str):
        return next((u for u in self.por_id.values() if u.email and u.email.value == email), None)

    async def save(self, usuario):
        self.por_id[usuario.id] = usuario
        return usuario


class SesionesFalsas:
    def __init__(self) -> None:
        self.por_id: dict[UUID, Sesion] = {}

    async def crear(self, sesion: Sesion) -> None:
        self.por_id[sesion.id] = sesion

    async def buscar_por_hash(self, token_hash: str):
        return next((s for s in self.por_id.values() if s.token_hash == token_hash), None)

    buscar_por_hash_para_actualizar = buscar_por_hash

    async def marcar_usada(self, sesion_id: UUID, reemplazada_por: UUID, ahora: datetime) -> None:
        sesion = self.por_id[sesion_id]
        sesion.used_at = ahora
        sesion.replaced_by = reemplazada_por

    async def revocar(self, sesion_id: UUID, ahora: datetime) -> None:
        sesion = self.por_id[sesion_id]
        if sesion.revoked_at is None:
            sesion.revoked_at = ahora

    async def revocar_familia(self, family_id: UUID, ahora: datetime) -> None:
        for sesion in self.por_id.values():
            if sesion.family_id == family_id and sesion.revoked_at is None:
                sesion.revoked_at = ahora

    async def revocar_todas_del_usuario(self, user_id: UUID, ahora: datetime) -> None:
        for sesion in self.por_id.values():
            if sesion.user_id == user_id and sesion.revoked_at is None:
                sesion.revoked_at = ahora


class EventosFalsos:
    def __init__(self) -> None:
        self.registros: list[tuple[str, UUID | None, dict | None]] = []

    async def registrar(self, evento: str, user_id: UUID | None, meta: dict | None = None) -> None:
        self.registros.append((evento, user_id, meta))

    def tipos(self) -> list[str]:
        return [evento for evento, _, _ in self.registros]


class UnitOfWorkFalso:
    def __init__(self) -> None:
        self.confirmaciones = 0

    async def confirmar(self) -> None:
        self.confirmaciones += 1


class PoliticasFalsas:
    def __init__(self, politica=None) -> None:
        self.politica = politica

    async def get_active(self):
        return self.politica


class ConsentimientosFalsos:
    def __init__(self) -> None:
        self.registros: list[tuple[UUID, UUID, datetime]] = []

    async def registrar(self, user_id: UUID, policy_id: UUID, ahora: datetime) -> None:
        self.registros.append((user_id, policy_id, ahora))
