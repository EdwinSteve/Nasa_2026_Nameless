import httpx
import pytest

from app.api import app
from app.modules.identidad.api.dependencies import get_consultar_politica, get_registrar_usuario
from app.modules.identidad.application.consultar_politica import ConsultarPoliticaVigente
from tests.unit.fakes import PoliticasFalsas
from tests.unit.test_registrar_usuario import POLITICA, Entorno

REGISTRO = "/api/v1/auth/registro"
POLITICA_VIGENTE = "/api/v1/politicas/vigente"

CUERPO = {
    "full_name": "Ernesto Ramírez",
    "phone": "300 123 4567",
    "email": "",
    "password": "MiFinca2026",
    "municipality": "41001",
    "district": None,
    "accepts_policy": True,
    "policy_version": "2026.1",
}


@pytest.fixture
def entorno():
    entorno = Entorno()
    app.dependency_overrides[get_registrar_usuario] = lambda: entorno.caso
    yield entorno
    app.dependency_overrides.clear()


@pytest.fixture
async def cliente(entorno):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as cliente:
        yield cliente


async def test_registro_responde_201_con_usuario_y_tokens(cliente):
    respuesta = await cliente.post(REGISTRO, json=CUERPO)

    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"user", "tokens"}
    assert cuerpo["user"]["phone"] == "+573001234567"
    assert cuerpo["user"]["role"] == "productor"
    assert cuerpo["tokens"]["token_type"] == "bearer"
    assert "MiFinca2026" not in respuesta.text


async def test_celular_duplicado_responde_409(cliente):
    await cliente.post(REGISTRO, json=CUERPO)

    respuesta = await cliente.post(REGISTRO, json=CUERPO)

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "USUARIO_CELULAR_DUPLICADO"


async def test_sin_consentimiento_responde_422(cliente):
    respuesta = await cliente.post(REGISTRO, json={**CUERPO, "accepts_policy": False})

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "CONSENTIMIENTO_REQUERIDO"


async def test_contrasena_sin_numero_responde_422_con_el_campo(cliente):
    respuesta = await cliente.post(REGISTRO, json={**CUERPO, "password": "solamenteletras"})

    assert respuesta.status_code == 422
    assert [d["field"] for d in respuesta.json()["details"]] == ["body.password"]


async def test_celular_fijo_no_se_acepta(cliente):
    respuesta = await cliente.post(REGISTRO, json={**CUERPO, "phone": "608 871 0000"})

    assert respuesta.status_code == 422


@pytest.mark.parametrize("politica, estado", [(POLITICA, 200), (None, 503)])
async def test_politica_vigente(politica, estado):
    app.dependency_overrides[get_consultar_politica] = lambda: ConsultarPoliticaVigente(
        politicas=PoliticasFalsas(politica)
    )
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as cliente:
            respuesta = await cliente.get(POLITICA_VIGENTE)
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == estado
    if estado == 200:
        assert respuesta.json() == {"version": "2026.1", "url_texto": "/politica-de-datos", "contenido": "Texto"}
    else:
        assert respuesta.json()["code"] == "POLITICA_NO_DISPONIBLE"


async def test_cors_permite_el_origen_de_la_ui():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as cliente:
        respuesta = await cliente.options(
            REGISTRO,
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

    assert respuesta.status_code == 200
    assert respuesta.headers["access-control-allow-origin"] == "http://localhost:3000"
