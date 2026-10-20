"""Diagnóstico satelital de un lote: cuatro pasos que corren en paralelo.

El estado general y el avance no se guardan: se calculan a partir de los pasos
cada vez que se consulta. Así cuatro tareas concurrentes nunca pisan un mismo campo.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID, uuid4


class CodigoPaso(str, Enum):
    CLIMA = "clima"
    HUMEDAD = "humedad"
    SUELO = "suelo"
    VERDOR = "verdor"


class EstadoPaso(str, Enum):
    PENDIENTE = "pendiente"
    EN_PROCESO = "en_proceso"
    LISTA = "lista"
    FALLIDA = "fallida"


@dataclass(frozen=True)
class DefinicionPaso:
    nombre: str
    fuente: str
    frase: str
    duracion_esperada_s: float   # solo para estimar la barra de avance
    tiempo_maximo_s: float       # pasado este tiempo el paso se da por fallido


PASOS: dict[CodigoPaso, DefinicionPaso] = {
    CodigoPaso.CLIMA: DefinicionPaso(
        "Clima de los últimos 45 años", "NASA POWER",
        "Revisando 45 años de clima de tu zona...", 8, 180,
    ),
    CodigoPaso.HUMEDAD: DefinicionPaso(
        "Humedad de la tierra", "NASA SMAP",
        "Midiendo la humedad de la tierra con el satélite SMAP...", 40, 300,
    ),
    CodigoPaso.SUELO: DefinicionPaso(
        "Tipo de suelo", "SoilGrids (ISRIC)",
        "Leyendo el tipo de suelo con SoilGrids...", 90, 600,
    ),
    CodigoPaso.VERDOR: DefinicionPaso(
        "Verdor del terreno", "NASA MODIS",
        "Mirando el verdor del terreno desde el espacio...", 45, 300,
    ),
}

MENSAJE_INICIO = "Conectando con los satélites para analizar tu lote..."
MENSAJE_LISTA = "¡Diagnóstico completo! Ya puedes ver tu lote."
MENSAJE_FALLIDA = "No pudimos leer los datos de los satélites. Intenta de nuevo en unos minutos."
MENSAJE_INTERRUMPIDO = "El análisis se interrumpió antes de terminar."
# Margen sobre tiempo_maximo_s antes de declarar un paso "colgado" (p. ej. si se reinició el servidor).
MARGEN_COLGADO = timedelta(seconds=60)


@dataclass
class Paso:
    codigo: CodigoPaso
    estado: EstadoPaso = EstadoPaso.PENDIENTE
    iniciado_en: datetime | None = None
    terminado_en: datetime | None = None
    resumen: str | None = None
    error: str | None = None
    datos: dict | None = None

    @property
    def definicion(self) -> DefinicionPaso:
        return PASOS[self.codigo]

    @property
    def terminado(self) -> bool:
        return self.estado in (EstadoPaso.LISTA, EstadoPaso.FALLIDA)

    def vigente(self, ahora: datetime) -> "Paso":
        """El paso tal como debe verse ahora: si quedó colgado, como fallido."""
        if self.estado is EstadoPaso.EN_PROCESO and self.iniciado_en is not None:
            limite = self.iniciado_en + timedelta(seconds=self.definicion.tiempo_maximo_s) + MARGEN_COLGADO
            if ahora > limite:
                return Paso(self.codigo, EstadoPaso.FALLIDA, self.iniciado_en, limite, None, MENSAJE_INTERRUMPIDO)
        return self

    def progreso(self, ahora: datetime) -> int:
        if self.terminado:
            return 100
        if self.estado is EstadoPaso.EN_PROCESO and self.iniciado_en is not None:
            transcurrido = (ahora - self.iniciado_en).total_seconds()
            # Sube rápido al principio y nunca llega a 100 hasta que el paso termina de verdad
            return min(95, 5 + round(90 * transcurrido / self.definicion.duracion_esperada_s))
        return 0


@dataclass
class Tarea:
    lote_id: UUID
    pasos: list[Paso] = field(default_factory=lambda: [Paso(c) for c in CodigoPaso])
    id: UUID = field(default_factory=uuid4)
    created_at: datetime | None = None

    def vigente(self, ahora: datetime) -> "Tarea":
        return Tarea(self.lote_id, [p.vigente(ahora) for p in self.pasos], self.id, self.created_at)

    def estado(self) -> EstadoPaso:
        if all(p.terminado for p in self.pasos):
            hay_lista = any(p.estado is EstadoPaso.LISTA for p in self.pasos)
            return EstadoPaso.LISTA if hay_lista else EstadoPaso.FALLIDA
        if all(p.estado is EstadoPaso.PENDIENTE for p in self.pasos):
            return EstadoPaso.PENDIENTE
        return EstadoPaso.EN_PROCESO

    def progreso(self, ahora: datetime) -> int:
        return round(sum(p.progreso(ahora) for p in self.pasos) / len(self.pasos))

    def paso_activo(self) -> Paso | None:
        """El primero en proceso, en el orden fijo de la pantalla."""
        return next((p for p in self.pasos if p.estado is EstadoPaso.EN_PROCESO), None)

    def mensaje(self) -> str:
        estado = self.estado()
        if estado is EstadoPaso.LISTA:
            return MENSAJE_LISTA
        if estado is EstadoPaso.FALLIDA:
            return MENSAJE_FALLIDA
        activo = self.paso_activo()
        return activo.definicion.frase if activo else MENSAJE_INICIO


@dataclass(frozen=True)
class ResultadoPaso:
    """Lo que devuelve el proveedor de datos al terminar un paso."""

    resumen: str          # frase para el productor
    datos: dict           # valores numéricos y su procedencia (para la ficha y el motor)


@dataclass(frozen=True)
class LoteDiagnostico:
    lote_id: UUID
    nombre: str
    area_ha: float
    poligono: dict
    lat: float
    lon: float
    municipio_nombre: str
    corregimiento_nombre: str
