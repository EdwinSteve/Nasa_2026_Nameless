from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.diagnostico.domain.entity import CodigoPaso, EstadoPaso, LoteDiagnostico, Paso, Tarea
from app.modules.diagnostico.infrastructure.orm_models import PasoORM, TareaORM
from app.modules.fincas.application.casos import ObtenerLote
from app.modules.fincas.domain.errors import LoteNoEncontrado

ORDEN = {codigo: i for i, codigo in enumerate(CodigoPaso)}


class SqlAlchemyTareaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def crear(self, tarea: Tarea) -> Tarea:
        self._session.add(TareaORM(id=tarea.id, lote_id=tarea.lote_id))
        await self._session.flush()  # la tarea debe existir antes que sus pasos (clave foránea)
        self._session.add_all(
            PasoORM(tarea_id=tarea.id, codigo=p.codigo.value, orden=ORDEN[p.codigo], estado=p.estado.value)
            for p in tarea.pasos
        )
        await self._session.flush()
        return await self.obtener(tarea.id)

    async def obtener(self, tarea_id: UUID) -> Tarea | None:
        fila = await self._session.get(TareaORM, tarea_id)
        if fila is None:
            return None
        pasos = (await self._session.execute(
            select(PasoORM).where(PasoORM.tarea_id == tarea_id).order_by(PasoORM.orden)
            .execution_options(populate_existing=True)
        )).scalars().all()
        return Tarea(
            lote_id=fila.lote_id,
            id=fila.id,
            created_at=fila.created_at,
            pasos=[
                Paso(
                    codigo=CodigoPaso(p.codigo),
                    estado=EstadoPaso(p.estado),
                    iniciado_en=p.iniciado_en,
                    terminado_en=p.terminado_en,
                    resumen=p.resumen,
                    error=p.error,
                    datos=p.datos,
                )
                for p in pasos
            ],
        )

    async def iniciar_paso(self, tarea_id: UUID, codigo: CodigoPaso, ahora: datetime) -> None:
        await self._session.execute(
            update(PasoORM)
            .where(PasoORM.tarea_id == tarea_id, PasoORM.codigo == codigo.value)
            .values(estado=EstadoPaso.EN_PROCESO.value, iniciado_en=ahora)
        )

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
        await self._session.execute(
            update(PasoORM)
            .where(PasoORM.tarea_id == tarea_id, PasoORM.codigo == codigo.value)
            .values(estado=estado.value, terminado_en=ahora, resumen=resumen, error=error, datos=datos)
        )


class SqlAlchemyUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def confirmar(self) -> None:
        await self._session.commit()


def fabrica_tareas(sesiones: Callable[[], AsyncSession]):
    """FabricaTareas sobre un async_sessionmaker: una sesión nueva por cada uso."""

    @asynccontextmanager
    async def abrir() -> AsyncIterator[tuple[SqlAlchemyTareaRepository, SqlAlchemyUnitOfWork]]:
        async with sesiones() as session:
            yield SqlAlchemyTareaRepository(session), SqlAlchemyUnitOfWork(session)

    return abrir


class LotesDesdeFincas:
    """Adaptador del puerto Lotes sobre el caso de uso ObtenerLote del módulo fincas."""

    def __init__(self, obtener_lote: ObtenerLote) -> None:
        self._obtener = obtener_lote

    async def para_diagnostico(self, propietario_id: UUID, lote_id: UUID) -> LoteDiagnostico | None:
        try:
            r = await self._obtener.ejecutar(propietario_id, lote_id)
        except LoteNoEncontrado:
            return None
        lat, lon = r.lote.poligono.centroide
        return LoteDiagnostico(
            lote_id=r.lote.id,
            nombre=r.lote.nombre,
            area_ha=r.lote.area_ha,
            poligono=r.lote.poligono.a_geojson(),
            lat=lat,
            lon=lon,
            municipio_nombre=r.municipio_nombre,
            corregimiento_nombre=r.centro_poblado_nombre,
        )


class RelojSistema:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
