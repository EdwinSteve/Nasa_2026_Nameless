"""Recomendación de cultivos del modelo predictivo (surco_ml, modelo A) para un lote.

El cálculo baja 45 años de clima del punto y corre el modelo: toma de segundos a minutos,
así que se pide (POST) y se consulta (GET) como el diagnóstico.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from uuid import UUID, uuid4

# Las fechas de siembra con que se entrenó el modelo
DIAS_SIEMBRA = (1, 16)
# Más que esto en proceso significa que el servidor se reinició a mitad del cálculo
TIEMPO_MAXIMO = timedelta(minutes=20)


class EstadoRecomendacion(str, Enum):
    EN_PROCESO = "en_proceso"
    LISTA = "lista"
    FALLIDA = "fallida"


@dataclass
class Recomendacion:
    lote_id: UUID
    fecha_siembra: date
    estado: EstadoRecomendacion = EstadoRecomendacion.EN_PROCESO
    resultado: dict | None = None    # lo que devuelve surco_ml.predecir.recomendar
    error: str | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime | None = None
    terminado_en: datetime | None = None

    def vigente(self, ahora: datetime) -> "Recomendacion":
        """Una recomendación colgada (p. ej. tras reiniciar el servidor) se ve como fallida."""
        if self.estado is EstadoRecomendacion.EN_PROCESO and self.created_at and ahora - self.created_at > TIEMPO_MAXIMO:
            return Recomendacion(
                self.lote_id, self.fecha_siembra, EstadoRecomendacion.FALLIDA, None,
                "El cálculo se interrumpió antes de terminar.", self.id, self.created_at, None,
            )
        return self


@dataclass(frozen=True)
class LoteRecomendacion:
    lote_id: UUID
    nombre: str
    lat: float
    lon: float
