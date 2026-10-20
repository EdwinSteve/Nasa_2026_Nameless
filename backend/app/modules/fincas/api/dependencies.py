from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.modules.fincas.application.casos import CrearFinca, CrearLote, GuardarPreferencias, ObtenerLote
from app.modules.fincas.infrastructure.repositories import (
    SqlAlchemyFincaRepository,
    SqlAlchemyLoteRepository,
    SqlAlchemyPreferenciasRepository,
    SqlAlchemyUnitOfWork,
    TerritorioDivipola,
)
from app.modules.territorio.api.dependencies import get_consultar_territorio

Sesion = Annotated[AsyncSession, Depends(get_session)]


def get_territorio() -> TerritorioDivipola:
    return TerritorioDivipola(get_consultar_territorio())


async def get_crear_finca(session: Sesion) -> CrearFinca:
    return CrearFinca(
        fincas=SqlAlchemyFincaRepository(session),
        territorio=get_territorio(),
        uow=SqlAlchemyUnitOfWork(session),
    )


async def get_crear_lote(session: Sesion) -> CrearLote:
    return CrearLote(
        fincas=SqlAlchemyFincaRepository(session),
        lotes=SqlAlchemyLoteRepository(session),
        uow=SqlAlchemyUnitOfWork(session),
    )


async def get_guardar_preferencias(session: Sesion) -> GuardarPreferencias:
    return GuardarPreferencias(
        preferencias=SqlAlchemyPreferenciasRepository(session),
        uow=SqlAlchemyUnitOfWork(session),
    )


async def get_obtener_lote(session: Sesion) -> ObtenerLote:
    return ObtenerLote(
        fincas=SqlAlchemyFincaRepository(session),
        lotes=SqlAlchemyLoteRepository(session),
        territorio=get_territorio(),
    )
