from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints, field_validator

from app.modules.fincas.domain.entity import Prioridad, TipoRiego

Nombre = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class CrearFincaRequest(BaseModel):
    nombre: Nombre = Field(..., examples=["La Esperanza"])
    municipio: str = Field(..., pattern=r"^\d{5}$", examples=["41001"], description="Código DIVIPOLA.")
    corregimiento: str = Field(
        ..., pattern=r"^\d{8}$", examples=["41001003"], description="Código DIVIPOLA del centro poblado (41001003 = Fortalecillas)."
    )
    vereda: Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None = None

    @field_validator("vereda", mode="before")
    @classmethod
    def _vacia_a_none(cls, v):
        return None if isinstance(v, str) and not v.strip() else v


class FincaResponse(BaseModel):
    id: UUID
    nombre: str


class PoligonoGeoJSON(BaseModel):
    type: Literal["Polygon"]
    coordinates: list[list[list[float]]] = Field(
        ..., description="Un solo anillo cerrado de [longitud, latitud] (EPSG:4326)."
    )


class CrearLoteRequest(BaseModel):
    nombre: Nombre = Field(..., examples=["Lote La Vega"])
    poligono: PoligonoGeoJSON
    tiene_riego: bool
    tipo_riego: TipoRiego | None = None
    cultivo_anterior: Annotated[str, StringConstraints(strip_whitespace=True, max_length=60)] | None = Field(
        None, examples=["maiz"], description="Lo sembrado el último semestre; null si es un lote nuevo."
    )


class LoteResponse(BaseModel):
    id: UUID
    nombre: str
    area_ha: float = Field(..., description="Calculada por el servidor sobre la esfera.")


class LoteDetalleResponse(LoteResponse):
    finca_id: UUID
    finca_nombre: str
    municipio_nombre: str
    corregimiento_nombre: str
    poligono: PoligonoGeoJSON
    centroide: tuple[float, float] = Field(..., description="(latitud, longitud)")
    tiene_riego: bool
    tipo_riego: TipoRiego | None
    cultivo_anterior: str | None


class GuardarPreferenciasRequest(BaseModel):
    orden: list[Prioridad] = Field(
        ...,
        min_length=4,
        max_length=4,
        examples=[["ahorro_agua", "ganar_mas", "cuidar_suelo", "arriesgar_menos"]],
        description="Las cuatro prioridades, de la más a la menos importante.",
    )
