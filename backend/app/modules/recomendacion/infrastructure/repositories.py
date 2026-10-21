from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.fincas.application.casos import ObtenerLote
from app.modules.fincas.domain.errors import LoteNoEncontrado
from app.modules.recomendacion.domain.entity import EstadoRecomendacion, LoteRecomendacion, Recomendacion
from app.modules.recomendacion.infrastructure.orm_models import RecomendacionORM


class SqlAlchemyRecomendacionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def crear(self, recomendacion: Recomendacion) -> Recomendacion:
        fila = RecomendacionORM(
            id=recomendacion.id,
            lote_id=recomendacion.lote_id,
            fecha_siembra=recomendacion.fecha_siembra,
            estado=recomendacion.estado.value,
        )
        self._session.add(fila)
        await self._session.flush()
        await self._session.refresh(fila)
        return _a_dominio(fila)

    async def obtener(self, recomendacion_id: UUID) -> Recomendacion | None:
        fila = await self._session.get(RecomendacionORM, recomendacion_id, populate_existing=True)
        return _a_dominio(fila) if fila else None

    async def terminar(
            self, recomendacion_id: UUID, estado: EstadoRecomendacion, ahora: datetime,
            resultado: dict | None = None, error: str | None = None,
    ) -> None:
        await self._session.execute(
            update(RecomendacionORM)
            .where(RecomendacionORM.id == recomendacion_id)
            .values(estado=estado.value, terminado_en=ahora, resultado=resultado, error=error)
        )


class SqlAlchemyUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def confirmar(self) -> None:
        await self._session.commit()


def fabrica_recomendaciones(sesiones: Callable[[], AsyncSession]):
    @asynccontextmanager
    async def abrir() -> AsyncIterator[tuple[SqlAlchemyRecomendacionRepository, SqlAlchemyUnitOfWork]]:
        async with sesiones() as session:
            yield SqlAlchemyRecomendacionRepository(session), SqlAlchemyUnitOfWork(session)

    return abrir


class LotesDesdeFincas:
    """Adaptador del puerto Lotes sobre el caso de uso ObtenerLote del módulo fincas."""

    def __init__(self, obtener_lote: ObtenerLote) -> None:
        self._obtener = obtener_lote

    async def para_recomendacion(self, propietario_id: UUID, lote_id: UUID) -> LoteRecomendacion | None:
        try:
            r = await self._obtener.ejecutar(propietario_id, lote_id)
        except LoteNoEncontrado:
            return None
        lat, lon = r.lote.poligono.centroide
        return LoteRecomendacion(lote_id=r.lote.id, nombre=r.lote.nombre, lat=lat, lon=lon)


class RelojSistema:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


def _a_dominio(fila: RecomendacionORM) -> Recomendacion:
    return Recomendacion(
        id=fila.id,
        lote_id=fila.lote_id,
        fecha_siembra=fila.fecha_siembra,
        estado=EstadoRecomendacion(fila.estado),
        resultado=fila.resultado,
        error=fila.error,
        created_at=fila.created_at,
        terminado_en=fila.terminado_en,
    )
