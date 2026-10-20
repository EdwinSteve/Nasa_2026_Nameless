from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.modules.fincas.api.dependencies import (
    get_crear_finca,
    get_crear_lote,
    get_guardar_preferencias,
    get_obtener_lote,
)
from app.modules.fincas.api.schemas import (
    CrearFincaRequest,
    CrearLoteRequest,
    FincaResponse,
    GuardarPreferenciasRequest,
    LoteDetalleResponse,
    LoteResponse,
)
from app.modules.fincas.application.casos import (
    CrearFinca,
    CrearLote,
    DatosFinca,
    DatosLote,
    GuardarPreferencias,
    ObtenerLote,
)
from app.modules.identidad.api.dependencies import usuario_actual
from app.modules.identidad.domain.entity import User

router = APIRouter(tags=["Fincas y lotes"])

Usuario = Annotated[User, Depends(usuario_actual)]
SIN_SESION = {401: {"description": "Falta el access token o no es válido."}}


@router.post(
    "/fincas",
    status_code=201,
    response_model=FincaResponse,
    summary="Registrar una finca del productor",
    responses={**SIN_SESION, 422: {"description": "FINCA_UBICACION_INVALIDA o VALIDATION."}},
)
async def crear_finca(
        body: CrearFincaRequest,
        usuario: Usuario,
        caso: Annotated[CrearFinca, Depends(get_crear_finca)],
) -> FincaResponse:
    finca = await caso.ejecutar(usuario.id, DatosFinca(**body.model_dump()))
    return FincaResponse(id=finca.id, nombre=finca.nombre)


@router.post(
    "/fincas/{finca_id}/lotes",
    status_code=201,
    response_model=LoteResponse,
    summary="Marcar un lote dentro de una finca",
    description="El servidor valida el polígono y calcula el área oficial del lote.",
    responses={
        **SIN_SESION,
        404: {"description": "FINCA_NO_ENCONTRADA (no existe o es de otro productor)."},
        422: {"description": "LOTE_POLIGONO_INVALIDO, LOTE_RIEGO_INCONSISTENTE o VALIDATION."},
    },
)
async def crear_lote(
        finca_id: UUID,
        body: CrearLoteRequest,
        usuario: Usuario,
        caso: Annotated[CrearLote, Depends(get_crear_lote)],
) -> LoteResponse:
    datos = DatosLote(
        nombre=body.nombre,
        poligono=body.poligono.model_dump(),
        tiene_riego=body.tiene_riego,
        tipo_riego=body.tipo_riego.value if body.tipo_riego else None,
        cultivo_anterior=body.cultivo_anterior or None,
    )
    lote = await caso.ejecutar(usuario.id, finca_id, datos)
    return LoteResponse(id=lote.id, nombre=lote.nombre, area_ha=lote.area_ha)


@router.get(
    "/lotes/{lote_id}",
    response_model=LoteDetalleResponse,
    summary="Detalle de un lote del productor",
    responses={**SIN_SESION, 404: {"description": "LOTE_NO_ENCONTRADO"}},
)
async def obtener_lote(
        lote_id: UUID,
        usuario: Usuario,
        caso: Annotated[ObtenerLote, Depends(get_obtener_lote)],
) -> LoteDetalleResponse:
    r = await caso.ejecutar(usuario.id, lote_id)
    return LoteDetalleResponse(
        id=r.lote.id,
        nombre=r.lote.nombre,
        area_ha=r.lote.area_ha,
        finca_id=r.finca.id,
        finca_nombre=r.finca.nombre,
        municipio_nombre=r.municipio_nombre,
        corregimiento_nombre=r.centro_poblado_nombre,
        poligono=r.lote.poligono.a_geojson(),
        centroide=r.lote.poligono.centroide,
        tiene_riego=r.lote.tiene_riego,
        tipo_riego=r.lote.tipo_riego,
        cultivo_anterior=r.lote.cultivo_anterior,
    )


@router.put(
    "/usuarios/me/preferencias",
    status_code=204,
    summary="Guardar el orden de prioridades del productor",
    responses={**SIN_SESION, 422: {"description": "PREFERENCIAS_INVALIDAS o VALIDATION."}},
)
async def guardar_preferencias(
        body: GuardarPreferenciasRequest,
        usuario: Usuario,
        caso: Annotated[GuardarPreferencias, Depends(get_guardar_preferencias)],
) -> Response:
    await caso.ejecutar(usuario.id, [p.value for p in body.orden])
    return Response(status_code=204)
