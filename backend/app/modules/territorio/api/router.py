from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.modules.territorio.api.dependencies import get_consultar_elevacion, get_consultar_territorio
from app.modules.territorio.api.schemas import CorregimientoItem, ElevacionResponse, MunicipioItem
from app.modules.territorio.application.consultas import ConsultarElevacion, ConsultarTerritorio

router = APIRouter(prefix="/territorio", tags=["Territorio"])

# Caja de Colombia continental e insular, con margen
LAT_MIN, LAT_MAX = -4.5, 13.5
LON_MIN, LON_MAX = -82.5, -66.0

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


@router.get(
    "/elevacion",
    response_model=ElevacionResponse,
    summary="Altitud de un punto y su municipio más cercano",
    description=(
        "Público: lo usa la bienvenida cuando el productor comparte su ubicación. La altitud sale del "
        "modelo NASA SRTM de 30 m; el municipio, del casco urbano o centro poblado DIVIPOLA más cercano "
        "(a menos de 15 km), así que es una aproximación."
    ),
    responses={503: {"description": "TERRITORIO_ELEVACION_NO_DISPONIBLE"}},
)
async def elevacion(
        caso: Annotated[ConsultarElevacion, Depends(get_consultar_elevacion)],
        lat: Annotated[float, Query(ge=LAT_MIN, le=LAT_MAX, examples=[2.93])],
        lon: Annotated[float, Query(ge=LON_MIN, le=LON_MAX, examples=[-75.28])],
) -> ElevacionResponse:
    r = await caso.ejecutar(lat, lon)
    return ElevacionResponse(
        altitud_msnm=r.altitud_msnm,
        fuente=r.fuente,
        municipio_codigo=r.municipio.codigo if r.municipio else None,
        municipio_nombre=r.municipio.nombre if r.municipio else None,
    )
