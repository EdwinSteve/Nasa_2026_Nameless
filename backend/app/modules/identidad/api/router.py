from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.modules.identidad.api.dependencies import (
    get_cerrar_sesion,
    get_iniciar_sesion,
    get_refrescar_sesion,
    usuario_actual,
    get_registrar_usuario,
    get_consultar_politica,
)
from app.modules.identidad.api.schemas import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    RegisterRequest,
    RegisterResponse,
    RegisteredUser,
    RegisterTokens,
    PoliticaVigenteResponse,
)
from app.modules.identidad.application.cerrar_sesion import CerrarSesion
from app.modules.identidad.application.iniciar_sesion import IniciarSesion
from app.modules.identidad.application.refrescar_sesion import RefrescarSesion
from app.modules.identidad.domain.entity import User
from app.modules.identidad.application.dto import DatosRegistro
from app.modules.identidad.application.registrar_usuario import RegistrarUsuario
from app.modules.identidad.application.consultar_politica import ConsultarPoliticaVigente
from app.core.config import get_settings

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
                "message": "La cuenta está temporalmente bloqueada por intentos fallidos. Inténtelo más tarde.",
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
                "message": "La sesión ya no es válida. Vuelva a iniciar sesión.",
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


@router.post(
    "/auth/logout",
    status_code=204,
    summary="Cerrar la sesión actual",
    description=(
        "Revoca el refresh token indicado. La app debe borrar ambos tokens del dispositivo. "
        "Responde 204 aunque el token ya estuviera revocado."
    ),
    responses={401: {"description": "Falta el access token o no es válido."}},
)
async def logout(
        body: LogoutRequest,
        usuario: Annotated[User, Depends(usuario_actual)],
        caso: Annotated[CerrarSesion, Depends(get_cerrar_sesion)],
) -> Response:
    await caso.una(usuario.id, body.refresh_token)
    return Response(status_code=204)


@router.post(
    "/auth/logout-todo",
    status_code=204,
    summary="Cerrar todas las sesiones del usuario",
    description="Revoca todos los refresh tokens del usuario, en todos sus dispositivos.",
    responses={401: {"description": "Falta el access token o no es válido."}},
)
async def logout_todo(
        usuario: Annotated[User, Depends(usuario_actual)],
        caso: Annotated[CerrarSesion, Depends(get_cerrar_sesion)],
) -> Response:
    await caso.todas(usuario.id)
    return Response(status_code=204)

@router.post(
    "/auth/registro",
    status_code=201,
    response_model=RegisterResponse,
    summary="Registrar un productor",
    description="Crea la cuenta y deja la sesión iniciada. Exige aceptar la política de privacidad vigente.",
    responses={
        409: {"description": "USUARIO_CELULAR_DUPLICADO, USUARIO_CORREO_DUPLICADO o POLITICA_DESACTUALIZADA."},
        422: {"description": "VALIDATION (datos inválidos) o CONSENTIMIENTO_REQUERIDO."},
    },
)
async def register(
        body: RegisterRequest,
        caso: Annotated[RegistrarUsuario, Depends(get_registrar_usuario)],
) -> RegisterResponse:
    resultado = await caso.ejecutar(DatosRegistro(**body.model_dump()))
    usuario, par = resultado.usuario, resultado.tokens
    return RegisterResponse(
        user=RegisteredUser(
            id=usuario.id,
            full_name=usuario.full_name,
            phone=usuario.phone.value,
            role=usuario.role,
            municipality=usuario.municipality,
            district=usuario.district,
        ),
        tokens=RegisterTokens(
            access_token=par.access_token,
            refresh_token=par.refresh_token,
            token_type=par.token_type,
            expires_in=par.expira_en,
        ),
    )


@router.get(
    "/politicas/vigente",
    response_model=PoliticaVigenteResponse,
    summary="Consultar la política de privacidad vigente",
    description="La UI la consulta al abrir el registro y envía su versión en policy_version.",
    responses={503: {"description": "POLITICA_NO_DISPONIBLE: no hay ninguna política activa."}},
)
async def politica_vigente(
        caso: Annotated[ConsultarPoliticaVigente, Depends(get_consultar_politica)],
) -> PoliticaVigenteResponse:
    politica = await caso.ejecutar()
    return PoliticaVigenteResponse(
        version=politica.version,
        url_texto=get_settings().politica_url,
        contenido=politica.contenido,
    )
