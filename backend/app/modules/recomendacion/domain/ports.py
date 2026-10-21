from contextlib import AbstractAsyncContextManager
from datetime import date, datetime
from typing import Protocol
from uuid import UUID

from app.modules.recomendacion.domain.entity import EstadoRecomendacion, LoteRecomendacion, Recomendacion


class RecomendacionRepository(Protocol):
    async def crear(self, recomendacion: Recomendacion) -> Recomendacion:
        ...

    async def obtener(self, recomendacion_id: UUID) -> Recomendacion | None:
        ...

    async def terminar(
            self, recomendacion_id: UUID, estado: EstadoRecomendacion, ahora: datetime,
            resultado: dict | None = None, error: str | None = None,
    ) -> None:
        ...


class UnitOfWork(Protocol):
    async def confirmar(self) -> None:
        ...


class FabricaRecomendaciones(Protocol):
    """Repositorio con su propia sesión: el cálculo corre después de responder la petición."""

    def __call__(self) -> AbstractAsyncContextManager[tuple[RecomendacionRepository, UnitOfWork]]:
        ...


class Lotes(Protocol):
    async def para_recomendacion(self, propietario_id: UUID, lote_id: UUID) -> LoteRecomendacion | None:
        ...


class ModeloPredictivo(Protocol):
    corrida: str

    def disponible(self) -> str | None:
        """None si el modelo está listo; si no, el motivo (p. ej. qué archivos faltan)."""
        ...

    def ultima_fecha(self) -> date:
        """La fecha de siembra más reciente con datos de clima suficientes."""
        ...

    async def recomendar(self, lat: float, lon: float, fecha: date) -> dict:
        ...


class Clock(Protocol):
    def now(self) -> datetime:
        ...
