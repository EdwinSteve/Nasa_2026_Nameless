"""Dobles en memoria para el módulo diagnostico."""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.modules.diagnostico.domain.entity import EstadoPaso, LoteDiagnostico, ResultadoPaso, Tarea
from tests.unit.fincas_fakes import POLIGONO

AHORA = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)
DUENO = uuid4()
LOTE = LoteDiagnostico(
    lote_id=uuid4(), nombre="La Vega", area_ha=32.74, poligono=POLIGONO, lat=2.9889, lon=-75.2912,
    municipio_nombre="Neiva", corregimiento_nombre="Fortalecillas",
)


class RelojFalso:
    def __init__(self, ahora: datetime = AHORA) -> None:
        self.ahora = ahora

    def now(self) -> datetime:
        return self.ahora


class LotesFalsos:
    def __init__(self, lote: LoteDiagnostico = LOTE, dueno: UUID = DUENO) -> None:
        self._lote, self._dueno = lote, dueno

    async def para_diagnostico(self, propietario_id, lote_id):
        return self._lote if (propietario_id, lote_id) == (self._dueno, self._lote.lote_id) else None


class TareasFalsas:
    def __init__(self) -> None:
        self.por_id: dict[UUID, Tarea] = {}

    async def crear(self, tarea):
        self.por_id[tarea.id] = tarea
        return tarea

    async def obtener(self, tarea_id):
        return self.por_id.get(tarea_id)

    def _reemplazar(self, tarea_id, codigo, **cambios):
        tarea = self.por_id[tarea_id]
        tarea.pasos = [replace(p, **cambios) if p.codigo == codigo else p for p in tarea.pasos]

    async def iniciar_paso(self, tarea_id, codigo, ahora):
        self._reemplazar(tarea_id, codigo, estado=EstadoPaso.EN_PROCESO, iniciado_en=ahora)

    async def terminar_paso(self, tarea_id, codigo, estado, ahora, resumen=None, error=None, datos=None):
        self._reemplazar(tarea_id, codigo, estado=estado, terminado_en=ahora, resumen=resumen, error=error, datos=datos)


class UnitOfWorkFalso:
    async def confirmar(self) -> None:
        pass


def fabrica(tareas: TareasFalsas):
    @asynccontextmanager
    async def abrir():
        yield tareas, UnitOfWorkFalso()

    return abrir


class ProveedorFalso:
    """Devuelve una frase fija por paso. `fallan` lista los pasos que lanzan error."""

    def __init__(self, fallan: tuple[str, ...] = ()) -> None:
        self.fallan = fallan
        self.llamados: list[str] = []
        self.en_vuelo = 0
        self.max_en_vuelo = 0

    async def _paso(self, codigo: str) -> ResultadoPaso:
        self.llamados.append(codigo)
        self.en_vuelo += 1
        self.max_en_vuelo = max(self.max_en_vuelo, self.en_vuelo)
        await asyncio.sleep(0.01)
        self.en_vuelo -= 1
        if codigo in self.fallan:
            raise ValueError(f"{codigo} no disponible")
        return ResultadoPaso(resumen=f"resumen de {codigo}", datos={"paso": codigo})

    async def clima(self, lote):
        return await self._paso("clima")

    async def humedad(self, lote):
        return await self._paso("humedad")

    async def suelo(self, lote):
        return await self._paso("suelo")

    async def verdor(self, lote):
        return await self._paso("verdor")
