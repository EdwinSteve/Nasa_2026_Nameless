import asyncio
import logging
from dataclasses import dataclass
from uuid import UUID

from app.modules.diagnostico.domain.entity import (
    PASOS,
    CodigoPaso,
    EstadoPaso,
    LoteDiagnostico,
    Tarea,
)
from app.modules.diagnostico.domain.errors import DiagnosticoNoEncontrado, LoteSinAcceso
from app.modules.diagnostico.domain.ports import Clock, FabricaTareas, Lotes, ProveedorDatos, TareaRepository, UnitOfWork

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VistaDiagnostico:
    tarea: Tarea          # ya "vigente": los pasos colgados aparecen como fallidos
    lote: LoteDiagnostico
    progreso: int
    progreso_por_paso: dict[CodigoPaso, int]


class IniciarDiagnostico:
    """Crea la tarea con sus cuatro pasos pendientes. Quien llama la ejecuta en segundo plano."""

    def __init__(self, *, lotes: Lotes, tareas: TareaRepository, uow: UnitOfWork) -> None:
        self._lotes = lotes
        self._tareas = tareas
        self._uow = uow

    async def ejecutar(self, propietario_id: UUID, lote_id: UUID) -> tuple[Tarea, LoteDiagnostico]:
        lote = await self._lotes.para_diagnostico(propietario_id, lote_id)
        if lote is None:
            raise LoteSinAcceso()
        tarea = await self._tareas.crear(Tarea(lote_id=lote.lote_id))
        await self._uow.confirmar()
        return tarea, lote


class EjecutarDiagnostico:
    """Corre los cuatro pasos en paralelo; cada uno guarda su resultado apenas termina,
    así la pantalla muestra el avance real y un paso lento no frena a los demás."""

    def __init__(self, *, proveedor: ProveedorDatos, fabrica: FabricaTareas, reloj: Clock) -> None:
        self._proveedor = proveedor
        self._fabrica = fabrica
        self._reloj = reloj

    async def ejecutar(self, tarea_id: UUID, lote: LoteDiagnostico) -> None:
        await asyncio.gather(*(self._paso(tarea_id, codigo, lote) for codigo in CodigoPaso))

    async def _paso(self, tarea_id: UUID, codigo: CodigoPaso, lote: LoteDiagnostico) -> None:
        async with self._fabrica() as (tareas, uow):
            await tareas.iniciar_paso(tarea_id, codigo, self._reloj.now())
            await uow.confirmar()

        consulta = getattr(self._proveedor, codigo.value)
        try:
            resultado = await asyncio.wait_for(consulta(lote), timeout=PASOS[codigo].tiempo_maximo_s)
        except Exception as exc:  # un dato faltante no tumba el diagnóstico: el paso queda fallido
            logger.warning("diagnostico_paso_fallido tarea=%s paso=%s error=%r", tarea_id, codigo.value, exc)
            terminado = dict(estado=EstadoPaso.FALLIDA, error=_mensaje_error(exc))
        else:
            terminado = dict(estado=EstadoPaso.LISTA, resumen=resultado.resumen, datos=resultado.datos)

        async with self._fabrica() as (tareas, uow):
            await tareas.terminar_paso(tarea_id, codigo, ahora=self._reloj.now(), **terminado)
            await uow.confirmar()


class ConsultarDiagnostico:
    def __init__(self, *, lotes: Lotes, tareas: TareaRepository, reloj: Clock) -> None:
        self._lotes = lotes
        self._tareas = tareas
        self._reloj = reloj

    async def ejecutar(self, propietario_id: UUID, lote_id: UUID, tarea_id: UUID) -> VistaDiagnostico:
        lote = await self._lotes.para_diagnostico(propietario_id, lote_id)
        if lote is None:
            raise LoteSinAcceso()
        tarea = await self._tareas.obtener(tarea_id)
        if tarea is None or tarea.lote_id != lote_id:
            raise DiagnosticoNoEncontrado()
        ahora = self._reloj.now()
        vigente = tarea.vigente(ahora)
        return VistaDiagnostico(
            tarea=vigente,
            lote=lote,
            progreso=vigente.progreso(ahora),
            progreso_por_paso={p.codigo: p.progreso(ahora) for p in vigente.pasos},
        )


def _mensaje_error(exc: Exception) -> str:
    """Texto corto para guardar; nunca se muestra tal cual al productor."""
    if isinstance(exc, TimeoutError):
        return "La fuente de datos tardó demasiado en responder."
    return f"{type(exc).__name__}: {exc}"[:300]
