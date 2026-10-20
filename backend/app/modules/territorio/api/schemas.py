from pydantic import BaseModel, Field


class MunicipioItem(BaseModel):
    codigo: str = Field(..., examples=["41001"], description="Código DIVIPOLA del municipio (5 dígitos).")
    nombre: str = Field(..., examples=["Neiva"])
    lat: float | None = Field(None, description="Centro del casco urbano, útil para centrar el mapa.")
    lon: float | None = None


class CorregimientoItem(BaseModel):
    codigo: str = Field(..., examples=["41001003"], description="Código DIVIPOLA del centro poblado (8 dígitos).")
    nombre: str = Field(..., examples=["Fortalecillas"])
    tipo: str = Field(..., description="cabecera (casco urbano) o centro_poblado (rural).")
    lat: float | None = None
    lon: float | None = None


class ElevacionResponse(BaseModel):
    altitud_msnm: float = Field(..., examples=[442])
    fuente: str = Field(..., examples=["NASA SRTM"])
    municipio_codigo: str | None = Field(None, examples=["41001"], description="Municipio DIVIPOLA más cercano.")
    municipio_nombre: str | None = Field(None, examples=["Neiva"])
