from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends

from app.modules.diagnostico.api.dependencies import (
    get_consultar_diagnostico,
    get_ejecutar_diagnostico,
    get_iniciar_diagnostico,
)
from app.modules.diagnostico.api.schemas import IniciarDiagnosticoResponse, PasoTarea, TareaDiagnosticoResponse
from app.modules.diagnostico.application.casos import ConsultarDiagnostico, EjecutarDiagnostico, IniciarDiagnostico
from app.modules.identidad.api.dependencies import usuario_actual
from app.modules.identidad.domain.entity import User

router = APIRouter(tags=["Diagnóstico"])

Usuario = Annotated[User, Depends(usuario_actual)]
SIN_SESION = {401: {"description": "Falta el access token o no es válido."}}


@router.post(
    "/lotes/{lote_id}/diagnostico",
    status_code=202,
    response_model=IniciarDiagnosticoResponse,
    summary="Iniciar el diagnóstico satelital del lote",
    description=(
        "Responde de inmediato con el id de la tarea. Clima (NASA POWER), humedad (SMAP), suelo (SoilGrids) "
        "y verdor (MODIS) se consultan en paralelo en segundo plano; el avance se lee con el GET."
    ),
    responses={**SIN_SESION, 404: {"description": "LOTE_NO_ENCONTRADO"}},
)
async def iniciar(
        lote_id: UUID,
        usuario: Usuario,
        tareas_fondo: BackgroundTasks,
        caso: Annotated[IniciarDiagnostico, Depends(get_iniciar_diagnostico)],
        ejecutor: Annotated[EjecutarDiagnostico, Depends(get_ejecutar_diagnostico)],
) -> IniciarDiagnosticoResponse:
    tarea, lote = await caso.ejecutar(usuario.id, lote_id)
    tareas_fondo.add_task(ejecutor.ejecutar, tarea.id, lote)
    return IniciarDiagnosticoResponse(tarea_id=tarea.id)


@router.get(
    "/lotes/{lote_id}/diagnostico/{tarea_id}",
    response_model=TareaDiagnosticoResponse,
    summary="Consultar el avance del diagnóstico",
    description="La UI lo consulta cada 2 s hasta que el estado sea lista o fallida.",
    responses={**SIN_SESION, 404: {"description": "LOTE_NO_ENCONTRADO o DIAGNOSTICO_NO_ENCONTRADO"}},
)
async def consultar(
        lote_id: UUID,
        tarea_id: UUID,
        usuario: Usuario,
        caso: Annotated[ConsultarDiagnostico, Depends(get_consultar_diagnostico)],
) -> TareaDiagnosticoResponse:
    vista = await caso.ejecutar(usuario.id, lote_id, tarea_id)
    tarea, lote = vista.tarea, vista.lote
    activo = tarea.paso_activo()
    return TareaDiagnosticoResponse(
        tarea_id=tarea.id,
        lote_id=lote.lote_id,
        nombre_lote=lote.nombre,
        area_ha=lote.area_ha,
        corregimiento_nombre=lote.corregimiento_nombre,
        municipio_nombre=lote.municipio_nombre,
        poligono=lote.poligono,
        estado=tarea.estado().value,
        progreso=vista.progreso,
        paso_activo_codigo=activo.codigo.value if activo else None,
        mensaje_estado=tarea.mensaje(),
        pasos=[
            PasoTarea(
                codigo=p.codigo.value,
                nombre=p.definicion.nombre,
                estado=p.estado.value,
                progreso=vista.progreso_por_paso[p.codigo],
                fuente=p.definicion.fuente,
                resumen=p.resumen if p.estado.value == "lista" else None,
            )
            for p in tarea.pasos
        ],
    )
