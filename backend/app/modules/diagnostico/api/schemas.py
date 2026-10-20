"""Mismo contrato que TareaDiagnosticoResponse en frontend/src/api/tipos.ts."""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

Codigo = Literal["clima", "humedad", "suelo", "verdor"]
Estado = Literal["pendiente", "en_proceso", "lista", "fallida"]


class IniciarDiagnosticoResponse(BaseModel):
    tarea_id: UUID


class PasoTarea(BaseModel):
    codigo: Codigo
    nombre: str = Field(..., description="Texto para el productor.")
    estado: Estado
    progreso: int = Field(..., ge=0, le=100)
    fuente: str = Field(..., examples=["NASA POWER"])
    resumen: str | None = Field(None, description="Frase con el dato, solo cuando el paso está listo.")


class TareaDiagnosticoResponse(BaseModel):
    tarea_id: UUID
    lote_id: UUID
    nombre_lote: str
    area_ha: float
    corregimiento_nombre: str
    municipio_nombre: str
    poligono: dict | None
    estado: Estado
    progreso: int = Field(..., ge=0, le=100)
    paso_activo_codigo: Codigo | None
    mensaje_estado: str
    pasos: list[PasoTarea]
