from uuid import UUID

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.fincas.domain.entity import Finca, Lote, Preferencias, TipoRiego
from app.modules.fincas.domain.values import Poligono
from app.modules.fincas.infrastructure.orm_models import FincaORM, LoteORM, PreferenciasORM
from app.modules.territorio.application.consultas import ConsultarTerritorio
from app.modules.territorio.domain.errors import MunicipioNoEncontrado


class SqlAlchemyFincaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def crear(self, finca: Finca) -> Finca:
        fila = FincaORM(
            id=finca.id,
            propietario_id=finca.propietario_id,
            nombre=finca.nombre,
            municipio=finca.municipio,
            centro_poblado=finca.centro_poblado,
            vereda=finca.vereda,
        )
        self._session.add(fila)
        await self._session.flush()
        await self._session.refresh(fila)
        return _finca(fila)

    async def obtener(self, finca_id: UUID) -> Finca | None:
        fila = await self._session.get(FincaORM, finca_id)
        return _finca(fila) if fila else None


class SqlAlchemyLoteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def crear(self, lote: Lote) -> Lote:
        lat, lon = lote.poligono.centroide
        fila = LoteORM(
            id=lote.id,
            finca_id=lote.finca_id,
            nombre=lote.nombre,
            poligono=lote.poligono.a_geojson(),
            area_ha=lote.area_ha,
            centroide_lat=lat,
            centroide_lon=lon,
            tiene_riego=lote.tiene_riego,
            tipo_riego=lote.tipo_riego.value if lote.tipo_riego else None,
            cultivo_anterior=lote.cultivo_anterior,
        )
        self._session.add(fila)
        await self._session.flush()
        await self._session.refresh(fila)
        return _lote(fila)

    async def obtener(self, lote_id: UUID) -> Lote | None:
        fila = await self._session.get(LoteORM, lote_id)
        return _lote(fila) if fila else None


class SqlAlchemyPreferenciasRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guardar(self, preferencias: Preferencias) -> None:
        orden = [p.value for p in preferencias.orden]
        stmt = insert(PreferenciasORM).values(usuario_id=preferencias.usuario_id, orden=orden)
        stmt = stmt.on_conflict_do_update(index_elements=["usuario_id"], set_={"orden": orden, "updated_at": func.now()})
        await self._session.execute(stmt)


class SqlAlchemyUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def confirmar(self) -> None:
        await self._session.commit()


class TerritorioDivipola:
    """Adaptador del puerto Territorio sobre el módulo territorio."""

    def __init__(self, consultas: ConsultarTerritorio) -> None:
        self._consultas = consultas

    def nombres(self, municipio: str, centro_poblado: str) -> tuple[str, str] | None:
        try:
            mun = self._consultas.municipio(municipio)
        except MunicipioNoEncontrado:  # para fincas es solo una ubicación inválida
            return None
        centro = self._consultas.centro_poblado(municipio, centro_poblado)
        if centro is None:
            return None
        return mun.nombre, ("Casco urbano" if centro.es_cabecera else centro.nombre)


def _finca(fila: FincaORM) -> Finca:
    return Finca(
        id=fila.id,
        propietario_id=fila.propietario_id,
        nombre=fila.nombre,
        municipio=fila.municipio,
        centro_poblado=fila.centro_poblado,
        vereda=fila.vereda,
        created_at=fila.created_at,
    )


def _lote(fila: LoteORM) -> Lote:
    return Lote(
        id=fila.id,
        finca_id=fila.finca_id,
        nombre=fila.nombre,
        poligono=Poligono.desde_geojson(fila.poligono),
        tiene_riego=fila.tiene_riego,
        tipo_riego=TipoRiego(fila.tipo_riego) if fila.tipo_riego else None,
        cultivo_anterior=fila.cultivo_anterior,
        created_at=fila.created_at,
    )
