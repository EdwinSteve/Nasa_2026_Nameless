import httpx
import pytest

from app.api import app
from app.modules.identidad.api.dependencies import get_cerrar_sesion, get_refrescar_sesion, get_user_repo
from app.modules.identidad.infrastructure.security.jwt_issuer import JwtTokenIssuer
from tests.unit.entorno import EntornoIdentidad

LOGOUT = "/api/v1/auth/logout"
LOGOUT_TODO = "/api/v1/auth/logout-todo"
REFRESH = "/api/v1/auth/refresh"


@pytest.fixture
def entorno():
    entorno = EntornoIdentidad()
    app.dependency_overrides[get_user_repo] = lambda: entorno.usuarios
    app.dependency_overrides[get_cerrar_sesion] = lambda: entorno.cerrar
    app.dependency_overrides[get_refrescar_sesion] = lambda: entorno.refrescar
    yield entorno
    app.dependency_overrides.clear()


@pytest.fixture
async def cliente(entorno):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as cliente:
        yield cliente


def _bearer(entorno) -> dict:
    token = JwtTokenIssuer().issue_access_token(entorno.usuario.id, "aprendiz")
    return {"Authorization": f"Bearer {token}"}


async def test_logout_responde_204_y_el_refresh_deja_de_servir(entorno, cliente):
    par = await entorno.login()

    respuesta = await cliente.post(
        LOGOUT, json={"refresh_token": par.refresh_token}, headers=_bearer(entorno)
    )
    despues = await cliente.post(REFRESH, json={"refresh_token": par.refresh_token})

    assert respuesta.status_code == 204
    assert respuesta.content == b""
    assert despues.status_code == 401
    assert despues.json()["code"] == "AUTH_REFRESH_INVALIDO"


async def test_logout_dos_veces_responde_204_ambas(entorno, cliente):
    par = await entorno.login()
    cuerpo = {"refresh_token": par.refresh_token}

    primera = await cliente.post(LOGOUT, json=cuerpo, headers=_bearer(entorno))
    segunda = await cliente.post(LOGOUT, json=cuerpo, headers=_bearer(entorno))

    assert primera.status_code == segunda.status_code == 204


async def test_logout_sin_token_de_acceso_responde_401_con_formato_del_proyecto(entorno, cliente):
    par = await entorno.login()

    respuesta = await cliente.post(LOGOUT, json={"refresh_token": par.refresh_token})

    assert respuesta.status_code == 401
    assert respuesta.json() == {"code": "AUTH_NO_AUTENTICADO", "message": "Falta el token de acceso."}


async def test_logout_todo_revoca_todas_las_sesiones(entorno, cliente):
    primera = await entorno.login()
    segunda = await entorno.login()

    respuesta = await cliente.post(LOGOUT_TODO, headers=_bearer(entorno))

    assert respuesta.status_code == 204
    for token in (primera.refresh_token, segunda.refresh_token):
        despues = await cliente.post(REFRESH, json={"refresh_token": token})
        assert despues.status_code == 401


async def test_logout_todo_sin_token_de_acceso_responde_401(entorno, cliente):
    respuesta = await cliente.post(LOGOUT_TODO)

    assert respuesta.status_code == 401
    assert respuesta.json()["code"] == "AUTH_NO_AUTENTICADO"
