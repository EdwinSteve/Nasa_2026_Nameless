from contextlib import AbstractAsyncContextManager
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.modules.diagnostico.domain.entity import CodigoPaso, EstadoPaso, LoteDiagnostico, ResultadoPaso, Tarea


class TareaRepository(Protocol):
    async def crear(self, tarea: Tarea) -> Tarea:
        ...

    async def obtener(self, tarea_id: UUID) -> Tarea | None:
        ...

    async def iniciar_paso(self, tarea_id: UUID, codigo: CodigoPaso, ahora: datetime) -> None:
        ...

    async def terminar_paso(
            self,
            tarea_id: UUID,
            codigo: CodigoPaso,
            estado: EstadoPaso,
            ahora: datetime,
            resumen: str | None = None,
            error: str | None = None,
            datos: dict | None = None,
    ) -> None:
        ...


class UnitOfWork(Protocol):
    async def confirmar(self) -> None:
        ...


class FabricaTareas(Protocol):
    """Abre un repositorio con su propia sesión de base de datos.

    Cada paso corre en paralelo y una sesión de SQLAlchemy no se puede usar desde
    dos corrutinas a la vez: por eso cada paso abre la suya.
    """

    def __call__(self) -> AbstractAsyncContextManager[tuple[TareaRepository, UnitOfWork]]:
        ...


class Lotes(Protocol):
    """Lo que el diagnóstico necesita del módulo fincas."""

    async def para_diagnostico(self, propietario_id: UUID, lote_id: UUID) -> LoteDiagnostico | None:
        ...


class ProveedorDatos(Protocol):
    """Una consulta por paso. Lanza una excepción si el dato no se pudo obtener."""

    async def clima(self, lote: LoteDiagnostico) -> ResultadoPaso:
        ...

    async def humedad(self, lote: LoteDiagnostico) -> ResultadoPaso:
        ...

    async def suelo(self, lote: LoteDiagnostico) -> ResultadoPaso:
        ...

    async def verdor(self, lote: LoteDiagnostico) -> ResultadoPaso:
        ...


class Clock(Protocol):
    def now(self) -> datetime:
        ...

