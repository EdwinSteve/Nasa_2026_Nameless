from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class SolicitarRecomendacionRequest(BaseModel):
    fecha_siembra: date | None = Field(
        None, examples=["2026-10-01"],
        description="Día 1 o 16. Si no se envía, la fecha más reciente con datos de clima ('si siembras ahora').",
    )


class SolicitarRecomendacionResponse(BaseModel):
    recomendacion_id: UUID
    fecha_siembra: date


class CultivoRecomendado(BaseModel):
    id: str = Field(..., examples=["maiz"])
    cultivo: str = Field(..., examples=["Maíz"])
    puntaje: float = Field(..., description="Idoneidad 0-1 esperada (mediana del modelo).")
    puntaje_min: float = Field(..., description="Escenario malo (p10).")
    puntaje_max: float = Field(..., description="Escenario bueno (p90).")
    prob_exito: float = Field(..., description="Probabilidad calibrada de completar el ciclo sin falla crítica.")
    de_cada_10: int = Field(..., description="La probabilidad como frecuencia: 'de cada 10 años, N salen bien'.")
    riego_neto_mm: float | None = Field(None, description="Agua que hay que aportar en todo el ciclo; null si el catálogo no tiene Kc.")
    riego_bruto_m3_ha: float | None = Field(None, description="Riego neto dividido por la eficiencia del sistema, en m³/ha.")
    dias_estres: float | None = None
    dias_ciclo: int


class CultivoDescartado(BaseModel):
    id: str
    cultivo: str
    motivo: str = Field(..., examples=["altitud 464 m fuera de 1200-2000 m"])


class ContextoLote(BaseModel):
    elevacion_m: float
    ph_0_30: float | None
    lluvia_90_dias_mm: float | None = None
    temperatura_90_dias_c: float | None = None
    oni: float | None = Field(None, description="Índice de El Niño en la fecha de siembra.")


class RecomendacionResponse(BaseModel):
    recomendacion_id: UUID
    lote_id: UUID
    nombre_lote: str
    fecha_siembra: date
    estado: Literal["en_proceso", "lista", "fallida"]
    mensaje: str
    cultivos: list[CultivoRecomendado] = []
    descartados: list[CultivoDescartado] = []
    contexto: ContextoLote | None = None
    modelo: str | None = None


class EstadoModeloResponse(BaseModel):
    disponible: bool
    corrida: str
    motivo: str | None = None
    ultima_fecha_siembra: date | None = None
