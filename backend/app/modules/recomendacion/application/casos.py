import asyncio
import logging
from datetime import date
from uuid import UUID

from app.modules.recomendacion.domain.entity import (
    DIAS_SIEMBRA,
    EstadoRecomendacion,
    LoteRecomendacion,
    Recomendacion,
)
from app.modules.recomendacion.domain.errors import (
    FechaSiembraInvalida,
    LoteSinAcceso,
    ModeloNoDisponible,
    RecomendacionNoEncontrada,
)
from app.modules.recomendacion.domain.ports import (
    Clock,
    FabricaRecomendaciones,
    Lotes,
    ModeloPredictivo,
    RecomendacionRepository,
    UnitOfWork,
)

logger = logging.getLogger(__name__)
TIEMPO_MAXIMO_CALCULO_S = 15 * 60


class SolicitarRecomendacion:
    """Valida el lote, la fecha y que el modelo esté disponible, y deja la recomendación en proceso."""

    def __init__(self, *, lotes: Lotes, recomendaciones: RecomendacionRepository, modelo: ModeloPredictivo,
                 uow: UnitOfWork) -> None:
        self._lotes = lotes
        self._recomendaciones = recomendaciones
        self._modelo = modelo
        self._uow = uow

    async def ejecutar(self, propietario_id: UUID, lote_id: UUID, fecha: date | None) -> tuple[Recomendacion, LoteRecomendacion]:
        lote = await self._lotes.para_recomendacion(propietario_id, lote_id)
        if lote is None:
            raise LoteSinAcceso()
        motivo = self._modelo.disponible()
        if motivo:
            raise ModeloNoDisponible(motivo)

        ultima = self._modelo.ultima_fecha()
        fecha = fecha or ultima
        if fecha.day not in DIAS_SIEMBRA:
            raise FechaSiembraInvalida("La fecha de siembra debe ser un día 1 o 16: así se entrenó el modelo.")
        if fecha > ultima:
            raise FechaSiembraInvalida(
                f"Todavía no hay datos de clima para esa fecha. La más reciente posible es {ultima.isoformat()}."
            )
        if fecha.year < 1982:
            raise FechaSiembraInvalida("El modelo necesita al menos un año de clima antes de la siembra (desde 1982).")

        recomendacion = await self._recomendaciones.crear(Recomendacion(lote_id=lote.lote_id, fecha_siembra=fecha))
        await self._uow.confirmar()
        return recomendacion, lote


class CalcularRecomendacion:
    def __init__(self, *, modelo: ModeloPredictivo, fabrica: FabricaRecomendaciones, reloj: Clock) -> None:
        self._modelo = modelo
        self._fabrica = fabrica
        self._reloj = reloj

    async def ejecutar(self, recomendacion_id: UUID, lote: LoteRecomendacion, fecha: date) -> None:
        try:
            resultado = await asyncio.wait_for(
                self._modelo.recomendar(lote.lat, lote.lon, fecha), timeout=TIEMPO_MAXIMO_CALCULO_S
            )
        except Exception as exc:  # el error queda guardado; la consulta lo muestra como fallida
            logger.warning("recomendacion_fallida id=%s error=%r", recomendacion_id, exc)
            terminado = dict(estado=EstadoRecomendacion.FALLIDA, error=f"{type(exc).__name__}: {exc}"[:500])
        else:
            terminado = dict(estado=EstadoRecomendacion.LISTA, resultado=resultado)

        async with self._fabrica() as (recomendaciones, uow):
            await recomendaciones.terminar(recomendacion_id, ahora=self._reloj.now(), **terminado)
            await uow.confirmar()


class ConsultarRecomendacion:
    def __init__(self, *, lotes: Lotes, recomendaciones: RecomendacionRepository, reloj: Clock) -> None:
        self._lotes = lotes
        self._recomendaciones = recomendaciones
        self._reloj = reloj

    async def ejecutar(self, propietario_id: UUID, lote_id: UUID, recomendacion_id: UUID) -> tuple[Recomendacion, LoteRecomendacion]:
        lote = await self._lotes.para_recomendacion(propietario_id, lote_id)
        if lote is None:
            raise LoteSinAcceso()
        recomendacion = await self._recomendaciones.obtener(recomendacion_id)
        if recomendacion is None or recomendacion.lote_id != lote_id:
            raise RecomendacionNoEncontrada()
        return recomendacion.vigente(self._reloj.now()), lote
