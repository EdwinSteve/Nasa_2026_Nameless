import httpx
import pytest

from app.api import app
from app.modules.identidad.api.dependencies import get_iniciar_sesion
from tests.unit.test_iniciar_sesion import CELULAR_E164, CONTRASENA, Entorno

RUTA = "/api/v1/auth/login"


@pytest.fixture
def entorno():
    entorno = Entorno()
    app.dependency_overrides[get_iniciar_sesion] = lambda: entorno.caso
    yield entorno
    app.dependency_overrides.clear()


@pytest.fixture
async def cliente(entorno):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as cliente:
        yield cliente


async def test_login_correcto_responde_200_con_el_contrato(cliente):
    respuesta = await cliente.post(RUTA, json={"celular": CELULAR_E164, "contrasena": CONTRASENA})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"access_token", "refresh_token", "token_type", "expira_en"}
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["expira_en"] == 900


async def test_login_acepta_celular_local_sin_prefijo(cliente):
    respuesta = await cliente.post(RUTA, json={"celular": "3001234567", "contrasena": CONTRASENA})

    assert respuesta.status_code == 200


async def test_contrasena_incorrecta_responde_401_con_codigo_y_mensaje(cliente):
    respuesta = await cliente.post(RUTA, json={"celular": CELULAR_E164, "contrasena": "mala"})

    assert respuesta.status_code == 401
    assert respuesta.json() == {
        "code": "AUTH_CREDENCIALES_INVALIDAS",
        "message": "El celular o la contraseña no son correctos.",
    }


async def test_celular_inexistente_responde_el_mismo_cuerpo_que_contrasena_mala(cliente):
    mala = await cliente.post(RUTA, json={"celular": CELULAR_E164, "contrasena": "mala"})
    inexistente = await cliente.post(RUTA, json={"celular": "+573009999999", "contrasena": CONTRASENA})

    assert inexistente.status_code == mala.status_code == 401
    assert inexistente.json() == mala.json()


async def test_cuenta_bloqueada_responde_423(cliente):
    for _ in range(5):
        await cliente.post(RUTA, json={"celular": CELULAR_E164, "contrasena": "mala"})

    respuesta = await cliente.post(RUTA, json={"celular": CELULAR_E164, "contrasena": CONTRASENA})

    assert respuesta.status_code == 423
    assert respuesta.json()["code"] == "AUTH_CUENTA_BLOQUEADA"


async def test_cuerpo_incompleto_responde_422_en_formato_del_proyecto(cliente):
    respuesta = await cliente.post(RUTA, json={"celular": CELULAR_E164})

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["code"] == "VALIDATION"
    assert any(detalle["field"].endswith("contrasena") for detalle in cuerpo["details"])


async def test_mensajes_de_error_no_contienen_la_contrasena(cliente):
    respuesta = await cliente.post(RUTA, json={"celular": CELULAR_E164, "contrasena": "claveSecreta99"})

    assert "claveSecreta99" not in respuesta.text
