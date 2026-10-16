from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.modules.identidad.domain.entity import Role, User
from app.modules.identidad.infrastructure.security.jwt_issuer import JwtTokenIssuer
from app.modules.identidad.infrastructure.persistences.repositories import (
    SqlAlchemyUserRepository,
)


async def get_user_repo(
        session: Annotated[AsyncSession, Depends(get_session)],
) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


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