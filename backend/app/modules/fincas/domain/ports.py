from typing import Protocol
from uuid import UUID

from app.modules.fincas.domain.entity import Finca, Lote, Preferencias


class FincaRepository(Protocol):
    async def crear(self, finca: Finca) -> Finca:
        ...

    async def obtener(self, finca_id: UUID) -> Finca | None:
        ...


class LoteRepository(Protocol):
    async def crear(self, lote: Lote) -> Lote:
        ...

    async def obtener(self, lote_id: UUID) -> Lote | None:
        ...


class PreferenciasRepository(Protocol):
    async def guardar(self, preferencias: Preferencias) -> None:
        """Reemplaza las preferencias anteriores del usuario."""
        ...


class Territorio(Protocol):
    """Lo que fincas necesita del catálogo DIVIPOLA (módulo territorio)."""

    def nombres(self, municipio: str, centro_poblado: str) -> tuple[str, str] | None:
        """(nombre del municipio, nombre del centro poblado), o None si no existen o no coinciden."""
        ...


class UnitOfWork(Protocol):
    async def confirmar(self) -> None:
        ...
