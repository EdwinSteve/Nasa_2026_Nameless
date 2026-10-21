import secrets
from functools import lru_cache
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_session
from app.core.errors import ErrorDominio
from app.modules.identidad.application.cerrar_sesion import CerrarSesion
from app.modules.identidad.application.iniciar_sesion import IniciarSesion
from app.modules.identidad.application.refrescar_sesion import RefrescarSesion
from app.modules.identidad.domain.entity import Role, User, UserStatus
from app.modules.identidad.infrastructure.persistences.repositories import (
    SqlAlchemyEventoRepository,
    SqlAlchemySesionRepository,
    SqlAlchemyUserRepository,
    SqlAlchemyPoliticaRepository,
    SqlAlchemyConsentimientoRepository

)
from app.modules.identidad.infrastructure.persistences.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from app.modules.identidad.infrastructure.security.hasher_argon2 import Argon2Hasher
from app.modules.identidad.infrastructure.security.jwt_issuer import JwtTokenIssuer
from app.modules.identidad.infrastructure.security.refresh_tokens import (
    GeneradorRefreshToken,
)
from app.modules.identidad.infrastructure.security.reloj import RelojSistema

from app.modules.identidad.application.registrar_usuario import RegistrarUsuario
from app.modules.identidad.application.consultar_politica import ConsultarPoliticaVigente

@lru_cache
def _hash_ficticio() -> str:
    """Hash de un valor aleatorio, calculado una vez. Se compara cuando el celular no existe
    para que la respuesta tarde lo mismo que un login real."""
    return Argon2Hasher().generate_hash(secrets.token_urlsafe(32))


async def get_user_repo(
        session: Annotated[AsyncSession, Depends(get_session)],
) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


async def get_iniciar_sesion(
        session: Annotated[AsyncSession, Depends(get_session)],
) -> IniciarSesion:
    """Composición del caso de uso con sus adaptadores reales."""
    settings = get_settings()
    return IniciarSesion(
        usuarios=SqlAlchemyUserRepository(session),
        sesiones=SqlAlchemySesionRepository(session),
        eventos=SqlAlchemyEventoRepository(session),
        hasher=Argon2Hasher(),
        hash_ficticio=_hash_ficticio(),
        tokens=JwtTokenIssuer(),
        generador=GeneradorRefreshToken(),
        reloj=RelojSistema(),
        uow=SqlAlchemyUnitOfWork(session),
        max_intentos=settings.login_max_intentos,
        bloqueo_minutos=settings.login_bloqueo_minutos,
        dias_refresh=settings.refresh_dias,
    )


async def get_refrescar_sesion(
        session: Annotated[AsyncSession, Depends(get_session)],
) -> RefrescarSesion:
    settings = get_settings()
    return RefrescarSesion(
        usuarios=SqlAlchemyUserRepository(session),
        sesiones=SqlAlchemySesionRepository(session),
        eventos=SqlAlchemyEventoRepository(session),
        tokens=JwtTokenIssuer(),
        generador=GeneradorRefreshToken(),
        reloj=RelojSistema(),
        uow=SqlAlchemyUnitOfWork(session),
        dias_refresh=settings.refresh_dias,
    )


async def get_cerrar_sesion(
        session: Annotated[AsyncSession, Depends(get_session)],
) -> CerrarSesion:
    return CerrarSesion(
        sesiones=SqlAlchemySesionRepository(session),
        eventos=SqlAlchemyEventoRepository(session),
        generador=GeneradorRefreshToken(),
        reloj=RelojSistema(),
        uow=SqlAlchemyUnitOfWork(session),
    )


async def usuario_actual(
        *,
        authorization: Annotated[str | None, Header()] = None,
        repo: Annotated[SqlAlchemyUserRepository, Depends(get_user_repo)],
) -> User:
    """Dependencia para rutas protegidas: valida el access token Bearer y devuelve el usuario."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise ErrorDominio("AUTH_NO_AUTENTICADO", "Falta el token de acceso.", 401)

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = JwtTokenIssuer().decode_access_token(token)
        usuario_id = UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise ErrorDominio("AUTH_TOKEN_INVALIDO", "Token inválido.", 401) from exc

    usuario = await repo.get_by_id(usuario_id)
    if usuario is None or usuario.status == UserStatus.INACTIVE:
        raise ErrorDominio("AUTH_USUARIO_NO_ENCONTRADO", "Usuario no encontrado.", 401)
    return usuario


def requiere_rol(*roles: Role):
    async def _checker(usuario: Annotated[User, Depends(usuario_actual)]) -> User:
        if usuario.role not in roles:
            raise ErrorDominio("AUTH_SIN_PERMISOS", "No tiene permisos para esta acción.", 403)
        return usuario

    return _checker

async def get_registrar_usuario(
        session: Annotated[AsyncSession, Depends(get_session)],
) -> RegistrarUsuario:
    settings = get_settings()
    return RegistrarUsuario(
        usuarios=SqlAlchemyUserRepository(session),
        politicas=SqlAlchemyPoliticaRepository(session),
        consentimientos=SqlAlchemyConsentimientoRepository(session),
        sesiones=SqlAlchemySesionRepository(session),
        eventos=SqlAlchemyEventoRepository(session),
        hasher=Argon2Hasher(),
        tokens=JwtTokenIssuer(),
        generador=GeneradorRefreshToken(),
        reloj=RelojSistema(),
        uow=SqlAlchemyUnitOfWork(session),
        dias_refresh=settings.refresh_dias,
    )

async def get_consultar_politica(
        session: Annotated[AsyncSession, Depends(get_session)],
) -> ConsultarPoliticaVigente:
    return ConsultarPoliticaVigente(politicas=SqlAlchemyPoliticaRepository(session))
