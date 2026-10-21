from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends

from app.modules.identidad.api.dependencies import usuario_actual
from app.modules.identidad.domain.entity import User
from app.modules.recomendacion.api.dependencies import get_calcular, get_consultar, get_modelo, get_solicitar
from app.modules.recomendacion.api.schemas import (
    ContextoLote,
    CultivoDescartado,
    CultivoRecomendado,
    EstadoModeloResponse,
    RecomendacionResponse,
    SolicitarRecomendacionRequest,
    SolicitarRecomendacionResponse,
)
from app.modules.recomendacion.application.casos import (
    CalcularRecomendacion,
    ConsultarRecomendacion,
    SolicitarRecomendacion,
)
from app.modules.recomendacion.domain.entity import EstadoRecomendacion
from app.modules.recomendacion.infrastructure.modelo_surco import ModeloSurco

router = APIRouter(tags=["Recomendación"])

Usuario = Annotated[User, Depends(usuario_actual)]
SIN_SESION = {401: {"description": "Falta el access token o no es válido."}}
TOP = 10

MENSAJES = {
    EstadoRecomendacion.EN_PROCESO: "Calculando con 45 años de clima de su lote...",
    EstadoRecomendacion.LISTA: "Estos son los cultivos con mejores probabilidades si siembras en esa fecha.",
    EstadoRecomendacion.FALLIDA: "No pudimos calcular la recomendación. Inténtelo de nuevo en unos minutos.",
}


@router.get(
    "/recomendaciones/modelo",
    response_model=EstadoModeloResponse,
    summary="¿Está disponible el modelo predictivo en este servidor?",
    description="Pública: la UI la usa para mostrar u ocultar la recomendación de cultivos.",
)
async def estado_modelo(modelo: Annotated[ModeloSurco, Depends(get_modelo)]) -> EstadoModeloResponse:
    motivo = modelo.disponible()
    return EstadoModeloResponse(
        disponible=motivo is None, corrida=modelo.corrida, motivo=motivo,
        ultima_fecha_siembra=None if motivo else modelo.ultima_fecha(),
    )


@router.post(
    "/lotes/{lote_id}/recomendaciones",
    status_code=202,
    response_model=SolicitarRecomendacionResponse,
    summary="Pedir la recomendación de cultivos para el lote",
    description="Responde de inmediato; el cálculo (datos del punto + modelo A) corre en segundo plano.",
    responses={
        **SIN_SESION,
        404: {"description": "LOTE_NO_ENCONTRADO"},
        422: {"description": "RECOMENDACION_FECHA_INVALIDA"},
        503: {"description": "RECOMENDACION_MODELO_NO_DISPONIBLE: faltan los archivos del modelo en el servidor."},
    },
)
async def solicitar(
        lote_id: UUID,
        usuario: Usuario,
        tareas_fondo: BackgroundTasks,
        caso: Annotated[SolicitarRecomendacion, Depends(get_solicitar)],
        calcular: Annotated[CalcularRecomendacion, Depends(get_calcular)],
        body: SolicitarRecomendacionRequest | None = None,
) -> SolicitarRecomendacionResponse:
    recomendacion, lote = await caso.ejecutar(usuario.id, lote_id, body.fecha_siembra if body else None)
    tareas_fondo.add_task(calcular.ejecutar, recomendacion.id, lote, recomendacion.fecha_siembra)
    return SolicitarRecomendacionResponse(recomendacion_id=recomendacion.id, fecha_siembra=recomendacion.fecha_siembra)


@router.get(
    "/lotes/{lote_id}/recomendaciones/{recomendacion_id}",
    response_model=RecomendacionResponse,
    summary="Consultar la recomendación de cultivos",
    responses={**SIN_SESION, 404: {"description": "LOTE_NO_ENCONTRADO o RECOMENDACION_NO_ENCONTRADA"}},
)
async def consultar(
        lote_id: UUID,
        recomendacion_id: UUID,
        usuario: Usuario,
        caso: Annotated[ConsultarRecomendacion, Depends(get_consultar)],
) -> RecomendacionResponse:
    recomendacion, lote = await caso.ejecutar(usuario.id, lote_id, recomendacion_id)
    respuesta = RecomendacionResponse(
        recomendacion_id=recomendacion.id,
        lote_id=lote.lote_id,
        nombre_lote=lote.nombre,
        fecha_siembra=recomendacion.fecha_siembra,
        estado=recomendacion.estado.value,
        mensaje=MENSAJES[recomendacion.estado],
    )
    r = recomendacion.resultado
    if recomendacion.estado is not EstadoRecomendacion.LISTA or not r:
        return respuesta

    eficiencia = r.get("eficiencia_riego") or 0.9
    pasan = sorted((x for x in r["resultados"] if x["pasa_filtros"]), key=lambda x: -x["puntaje_p50"])
    respuesta.cultivos = [
        CultivoRecomendado(
            id=x["id"], cultivo=x["cultivo"], puntaje=round(x["puntaje_p50"], 3),
            puntaje_min=round(x["puntaje_p10"], 3), puntaje_max=round(x["puntaje_p90"], 3),
            prob_exito=round(x["prob_exito"], 3), de_cada_10=round(10 * x["prob_exito"]),
            riego_neto_mm=None if x["riego_neto_mm"] is None else round(x["riego_neto_mm"]),
            riego_bruto_m3_ha=None if x["riego_neto_mm"] is None else round(x["riego_neto_mm"] / eficiencia * 10),
            dias_estres=None if x["dias_estres"] is None else round(x["dias_estres"]),
            dias_ciclo=x["dias_ciclo"],
        )
        for x in pasan[:TOP]
    ]
    respuesta.descartados = [
        CultivoDescartado(id=x["id"], cultivo=x["cultivo"], motivo=x["motivo"])
        for x in r["resultados"] if not x["pasa_filtros"]
    ]
    f = r.get("features_resumen", {})
    respuesta.contexto = ContextoLote(
        elevacion_m=round(r["elevacion_m"]), ph_0_30=None if r.get("ph_0_30") is None else round(r["ph_0_30"], 1),
        lluvia_90_dias_mm=f.get("f_lluvia_90"), temperatura_90_dias_c=f.get("f_t_media_90"), oni=f.get("f_oni"),
    )
    respuesta.modelo = r.get("corrida")
    return respuesta
