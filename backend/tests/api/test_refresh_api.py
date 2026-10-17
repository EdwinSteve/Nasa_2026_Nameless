import httpx
import pytest

from app.api import app
from app.modules.identidad.api.dependencies import get_refrescar_sesion
from tests.unit.entorno import EntornoIdentidad

RUTA = "/api/v1/auth/refresh"


@pytest.fixture
def entorno():
    entorno = EntornoIdentidad()
    app.dependency_overrides[get_refrescar_sesion] = lambda: entorno.refrescar
    yield entorno
    app.dependency_overrides.clear()


@pytest.fixture
async def cliente(entorno):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as cliente:
        yield cliente


async def test_refresh_valido_responde_200_con_el_contrato(entorno, cliente):
    inicio = await entorno.login()

    respuesta = await cliente.post(RUTA, json={"refresh_token": inicio.refresh_token})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"access_token", "refresh_token", "token_type", "expira_en"}
    assert cuerpo["refresh_token"] != inicio.refresh_token
    assert cuerpo["expira_en"] == 900


async def test_refresh_reutilizado_responde_401_con_codigo(entorno, cliente):
    inicio = await entorno.login()
    await cliente.post(RUTA, json={"refresh_token": inicio.refresh_token})

    respuesta = await cliente.post(RUTA, json={"refresh_token": inicio.refresh_token})

    assert respuesta.status_code == 401
    assert respuesta.json()["code"] == "AUTH_REFRESH_INVALIDO"


async def test_refresh_sin_campo_responde_422(cliente):
    respuesta = await cliente.post(RUTA, json={})

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "VALIDATION"
