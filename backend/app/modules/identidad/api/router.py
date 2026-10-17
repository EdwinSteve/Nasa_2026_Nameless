from typing import Annotated

from fastapi import APIRouter, Depends

from app.modules.identidad.api.dependencies import get_iniciar_sesion, get_refrescar_sesion
from app.modules.identidad.api.schemas import LoginRequest, RefreshRequest, TokenResponse
from app.modules.identidad.application.iniciar_sesion import IniciarSesion
from app.modules.identidad.application.refrescar_sesion import RefrescarSesion

router = APIRouter(
    tags=["Identidad"],
)

ERROR_CREDENCIALES = {
    "description": "Celular o contraseña incorrectos. Mismo mensaje si el celular no existe.",
    "content": {
        "application/json": {
            "example": {
                "code": "AUTH_CREDENCIALES_INVALIDAS",
                "message": "El celular o la contraseña no son correctos.",
            }
        }
    },
}

ERROR_BLOQUEADA = {
    "description": "Cuenta bloqueada 15 minutos tras 5 intentos fallidos.",
    "content": {
        "application/json": {
            "example": {
                "code": "AUTH_CUENTA_BLOQUEADA",
                "message": "La cuenta está temporalmente bloqueada por intentos fallidos. Intenta más tarde.",
            }
        }
    },
}


@router.get(
    "/auth/status",
    summary="Consultar disponibilidad del módulo de autenticación",
)
async def estado_auth():
    return {
        "status": "available",
        "module": "identidad",
    }


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Iniciar sesión con celular y contraseña",
    responses={401: ERROR_CREDENCIALES, 423: ERROR_BLOQUEADA},
)
async def login(
        body: LoginRequest,
        caso: Annotated[IniciarSesion, Depends(get_iniciar_sesion)],
) -> TokenResponse:
    par = await caso.ejecutar(body.celular, body.contrasena)
    return TokenResponse(
        access_token=par.access_token,
        refresh_token=par.refresh_token,
        token_type=par.token_type,
        expira_en=par.expira_en,
    )


ERROR_REFRESH = {
    "description": "El refresh token no existe, expiró, fue revocado o ya se usó.",
    "content": {
        "application/json": {
            "example": {
                "code": "AUTH_REFRESH_INVALIDO",
                "message": "La sesión ya no es válida. Vuelve a iniciar sesión.",
            }
        }
    },
}


@router.post(
    "/auth/refresh",
    response_model=TokenResponse,
    summary="Renovar la sesión con el refresh token",
    description=(
        "Devuelve un access token y un refresh token nuevos. El refresh token anterior "
        "queda inutilizable. Si se reutiliza uno ya usado, se cierran todas las sesiones de esa cadena."
    ),
    responses={401: ERROR_REFRESH},
)
async def refresh(
        body: RefreshRequest,
        caso: Annotated[RefrescarSesion, Depends(get_refrescar_sesion)],
) -> TokenResponse:
    par = await caso.ejecutar(body.refresh_token)
    return TokenResponse(
        access_token=par.access_token,
        refresh_token=par.refresh_token,
        token_type=par.token_type,
        expira_en=par.expira_en,
    )
