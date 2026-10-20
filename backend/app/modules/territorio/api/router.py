from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.modules.territorio.api.dependencies import get_consultar_territorio
from app.modules.territorio.api.schemas import CorregimientoItem, MunicipioItem
from app.modules.territorio.application.consultas import ConsultarTerritorio

router = APIRouter(prefix="/territorio", tags=["Territorio"])

Territorio = Annotated[ConsultarTerritorio, Depends(get_consultar_territorio)]


@router.get(
    "/municipios",
    response_model=list[MunicipioItem],
    summary="Municipios de un departamento (DIVIPOLA)",
    description="Público: la UI lo usa en el paso 1 del registro, antes de tener sesión. Hoy solo está cargado el Huila (41).",
    responses={404: {"description": "TERRITORIO_DEPARTAMENTO_NO_DISPONIBLE"}},
)
async def municipios(
        territorio: Territorio,
        departamento: Annotated[str, Query(pattern=r"^\d{2}$", examples=["41"])] = "41",
) -> list[MunicipioItem]:
    return [
        MunicipioItem(codigo=m.codigo, nombre=m.nombre, lat=m.lat, lon=m.lon)
        for m in territorio.municipios(departamento)
    ]


@router.get(
    "/municipios/{municipio}/corregimientos",
    response_model=list[CorregimientoItem],
    summary="Casco urbano y centros poblados de un municipio",
    description="Primero el casco urbano y luego los centros poblados rurales en orden alfabético.",
    responses={404: {"description": "TERRITORIO_MUNICIPIO_NO_ENCONTRADO"}},
)
async def corregimientos(municipio: str, territorio: Territorio) -> list[CorregimientoItem]:
    return [
        CorregimientoItem(
            codigo=c.codigo,
            nombre="Casco urbano" if c.es_cabecera else c.nombre,
            tipo="cabecera" if c.es_cabecera else "centro_poblado",
            lat=c.lat,
            lon=c.lon,
        )
        for c in territorio.centros_poblados(municipio)
    ]
