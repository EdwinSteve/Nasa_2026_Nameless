import secrets
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_session
from app.modules.identidad.application.iniciar_sesion import IniciarSesion
from app.modules.identidad.domain.entity import Role, User
from app.modules.identidad.infrastructure.persistences.repositories import (
    SqlAlchemyEventoRepository,
    SqlAlchemySesionRepository,
    SqlAlchemyUserRepository,
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


async def usuario_actual(
        authorization: Annotated[str | None, Header()] = None,
        repo: Annotated[SqlAlchemyUserRepository, Depends(get_user_repo)] = ...,
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_NO_AUTENTICADO", "message": "Falta el token."},
        )
    token = authorization.split(" ", 1)[1]
    issuer = JwtTokenIssuer()
    try:
        payload = issuer.decode_access_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_TOKEN_INVALIDO", "message": "Token inválido."},
        ) from exc

    user = await repo.get_by_id(payload["sub"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_USUARIO_NO_ENCONTRADO", "message": "Usuario no encontrado."},
        )
    return user


def requiere_rol(*roles: Role):
    async def _checker(user: Annotated[User, Depends(usuario_actual)]) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "AUTH_SIN_PERMISOS",
                    "message": "No tienes permisos para esta acción.",
                },
            )
        return user

    return _checker
