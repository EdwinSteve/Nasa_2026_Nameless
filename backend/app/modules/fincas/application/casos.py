from dataclasses import dataclass
from uuid import UUID

from app.modules.fincas.domain.entity import Finca, Lote, Preferencias, Prioridad, TipoRiego
from app.modules.fincas.domain.errors import (
    FincaNoEncontrada,
    LoteNoEncontrado,
    PrioridadesInvalidas,
    RiegoInconsistente,
    UbicacionInvalida,
)
from app.modules.fincas.domain.ports import (
    FincaRepository,
    LoteRepository,
    PreferenciasRepository,
    Territorio,
    UnitOfWork,
)
from app.modules.fincas.domain.values import Poligono


@dataclass(frozen=True)
class DatosFinca:
    nombre: str
    municipio: str
    corregimiento: str
    vereda: str | None


@dataclass(frozen=True)
class DatosLote:
    nombre: str
    poligono: dict
    tiene_riego: bool
    tipo_riego: str | None
    cultivo_anterior: str | None


@dataclass(frozen=True)
class LoteConUbicacion:
    """Lo que necesita el diagnóstico: el lote y dónde queda, con nombres legibles."""

    lote: Lote
    finca: Finca
    municipio_nombre: str
    centro_poblado_nombre: str


class CrearFinca:
    def __init__(self, *, fincas: FincaRepository, territorio: Territorio, uow: UnitOfWork) -> None:
        self._fincas = fincas
        self._territorio = territorio
        self._uow = uow

    async def ejecutar(self, propietario_id: UUID, datos: DatosFinca) -> Finca:
        if self._territorio.nombres(datos.municipio, datos.corregimiento) is None:
            raise UbicacionInvalida("El municipio o el corregimiento no existen, o no corresponden entre sí.")
        finca = await self._fincas.crear(
            Finca(
                propietario_id=propietario_id,
                nombre=datos.nombre,
                municipio=datos.municipio,
                centro_poblado=datos.corregimiento,
                vereda=datos.vereda,
            )
        )
        await self._uow.confirmar()
        return finca


class CrearLote:
    def __init__(self, *, fincas: FincaRepository, lotes: LoteRepository, uow: UnitOfWork) -> None:
        self._fincas = fincas
        self._lotes = lotes
        self._uow = uow

    async def ejecutar(self, propietario_id: UUID, finca_id: UUID, datos: DatosLote) -> Lote:
        finca = await self._fincas.obtener(finca_id)
        if finca is None or finca.propietario_id != propietario_id:
            raise FincaNoEncontrada()
        if datos.tiene_riego and datos.tipo_riego is None:
            raise RiegoInconsistente()
        lote = await self._lotes.crear(
            Lote(
                finca_id=finca.id,
                nombre=datos.nombre,
                poligono=Poligono.desde_geojson(datos.poligono),
                tiene_riego=datos.tiene_riego,
                # Sin riego, el tipo no aplica aunque la UI lo envíe.
                tipo_riego=TipoRiego(datos.tipo_riego) if datos.tiene_riego else None,
                cultivo_anterior=datos.cultivo_anterior,
            )
        )
        await self._uow.confirmar()
        return lote


class GuardarPreferencias:
    def __init__(self, *, preferencias: PreferenciasRepository, uow: UnitOfWork) -> None:
        self._preferencias = preferencias
        self._uow = uow

    async def ejecutar(self, usuario_id: UUID, orden: list[str]) -> Preferencias:
        try:
            prioridades = tuple(Prioridad(p) for p in orden)
        except ValueError as exc:
            raise PrioridadesInvalidas() from exc
        if sorted(prioridades) != sorted(Prioridad):
            raise PrioridadesInvalidas()
        preferencias = Preferencias(usuario_id=usuario_id, orden=prioridades)
        await self._preferencias.guardar(preferencias)
        await self._uow.confirmar()
        return preferencias


class ObtenerLote:
    def __init__(self, *, fincas: FincaRepository, lotes: LoteRepository, territorio: Territorio) -> None:
        self._fincas = fincas
        self._lotes = lotes
        self._territorio = territorio

    async def ejecutar(self, propietario_id: UUID, lote_id: UUID) -> LoteConUbicacion:
        lote = await self._lotes.obtener(lote_id)
        finca = await self._fincas.obtener(lote.finca_id) if lote else None
        if lote is None or finca is None or finca.propietario_id != propietario_id:
            raise LoteNoEncontrado()
        municipio, centro = self._territorio.nombres(finca.municipio, finca.centro_poblado) or ("", "")
        return LoteConUbicacion(lote=lote, finca=finca, municipio_nombre=municipio, centro_poblado_nombre=centro)
