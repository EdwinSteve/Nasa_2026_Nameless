from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import SessionLocal, get_session
from app.modules.diagnostico.application.casos import ConsultarDiagnostico, EjecutarDiagnostico, IniciarDiagnostico
from app.modules.diagnostico.infrastructure.proveedor_datos_tierra import ProveedorDatosTierra
from app.modules.diagnostico.infrastructure.repositories import (
    LotesDesdeFincas,
    RelojSistema,
    SqlAlchemyTareaRepository,
    SqlAlchemyUnitOfWork,
    fabrica_tareas,
)
from app.modules.fincas.api.dependencies import get_obtener_lote
from app.modules.fincas.application.casos import ObtenerLote

Sesion = Annotated[AsyncSession, Depends(get_session)]


async def get_lotes(obtener: Annotated[ObtenerLote, Depends(get_obtener_lote)]) -> LotesDesdeFincas:
    return LotesDesdeFincas(obtener)


async def get_iniciar_diagnostico(
        session: Sesion, lotes: Annotated[LotesDesdeFincas, Depends(get_lotes)]
) -> IniciarDiagnostico:
    return IniciarDiagnostico(lotes=lotes, tareas=SqlAlchemyTareaRepository(session), uow=SqlAlchemyUnitOfWork(session))


async def get_consultar_diagnostico(
        session: Sesion, lotes: Annotated[LotesDesdeFincas, Depends(get_lotes)]
) -> ConsultarDiagnostico:
    return ConsultarDiagnostico(lotes=lotes, tareas=SqlAlchemyTareaRepository(session), reloj=RelojSistema())


@lru_cache
def get_ejecutar_diagnostico() -> EjecutarDiagnostico:
    """Corre después de responder la petición: no puede usar la sesión de la petición,
    así que abre las suyas con SessionLocal."""
    return EjecutarDiagnostico(
        proveedor=ProveedorDatosTierra(get_settings().gee_project),
        fabrica=fabrica_tareas(SessionLocal),
        reloj=RelojSistema(),
    )
