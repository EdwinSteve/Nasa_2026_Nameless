from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import SessionLocal, get_session
from app.modules.fincas.api.dependencies import get_obtener_lote
from app.modules.fincas.application.casos import ObtenerLote
from app.modules.recomendacion.application.casos import (
    CalcularRecomendacion,
    ConsultarRecomendacion,
    SolicitarRecomendacion,
)
from app.modules.recomendacion.infrastructure.modelo_surco import ModeloSurco
from app.modules.recomendacion.infrastructure.repositories import (
    LotesDesdeFincas,
    RelojSistema,
    SqlAlchemyRecomendacionRepository,
    SqlAlchemyUnitOfWork,
    fabrica_recomendaciones,
)

Sesion = Annotated[AsyncSession, Depends(get_session)]


@lru_cache
def get_modelo() -> ModeloSurco:
    settings = get_settings()
    return ModeloSurco(corrida=settings.modelo_corrida, gee_project=settings.gee_project)


async def get_lotes(obtener: Annotated[ObtenerLote, Depends(get_obtener_lote)]) -> LotesDesdeFincas:
    return LotesDesdeFincas(obtener)


async def get_solicitar(
        session: Sesion, lotes: Annotated[LotesDesdeFincas, Depends(get_lotes)],
        modelo: Annotated[ModeloSurco, Depends(get_modelo)],
) -> SolicitarRecomendacion:
    return SolicitarRecomendacion(
        lotes=lotes, recomendaciones=SqlAlchemyRecomendacionRepository(session), modelo=modelo,
        uow=SqlAlchemyUnitOfWork(session),
    )


async def get_consultar(session: Sesion, lotes: Annotated[LotesDesdeFincas, Depends(get_lotes)]) -> ConsultarRecomendacion:
    return ConsultarRecomendacion(lotes=lotes, recomendaciones=SqlAlchemyRecomendacionRepository(session), reloj=RelojSistema())


async def get_calcular(modelo: Annotated[ModeloSurco, Depends(get_modelo)]) -> CalcularRecomendacion:
    """Corre después de responder: abre sus propias sesiones con SessionLocal."""
    return CalcularRecomendacion(modelo=modelo, fabrica=fabrica_recomendaciones(SessionLocal), reloj=RelojSistema())
