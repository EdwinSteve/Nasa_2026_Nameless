import httpx
import pytest
from sqlalchemy import text

REGISTRO = "/api/v1/auth/registro"
LOGIN = "/api/v1/auth/login"
POLITICA = "/api/v1/politicas/vigente"

CUERPO = {
    "full_name": "Ernesto Ramírez",
    "phone": "300 123 4567",
    "email": None,
    "password": "MiFinca2026",
    "municipality": "41001",
    "district": None,
    "accepts_policy": True,
    "policy_version": "2026.1",
}


@pytest.fixture
async def cliente(app_db):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app_db), base_url="http://test") as c:
        yield c


async def test_politica_vigente_es_la_sembrada_por_la_migracion(cliente):
    respuesta = await cliente.get(POLITICA)

    assert respuesta.status_code == 200
    assert respuesta.json()["version"] == "2026.1"


@pytest.mark.parametrize("email", [None, "ernesto@finca.co"])
async def test_registro_guarda_usuario_consentimiento_y_sesion_y_permite_login(cliente, sesion_maker, email):
    respuesta = await cliente.post(REGISTRO, json={**CUERPO, "email": email})
    assert respuesta.status_code == 201, respuesta.text

    async with sesion_maker() as sesion:
        usuario = (await sesion.execute(text(
            "SELECT phone, email, role, status, municipality FROM identidad.usuarios"
        ))).mappings().one()
        consentimientos = (await sesion.execute(text("SELECT count(*) FROM identidad.consentimientos"))).scalar_one()
        sesiones = (await sesion.execute(text("SELECT count(*) FROM identidad.sesiones"))).scalar_one()
    assert dict(usuario) == {
        "phone": "+573001234567", "email": email, "role": "productor", "status": "activo", "municipality": "41001",
    }
    assert consentimientos == 1
    assert sesiones == 1

    login = await cliente.post(LOGIN, json={"celular": "3001234567", "contrasena": "MiFinca2026"})
    assert login.status_code == 200


async def test_celular_duplicado_responde_409_sin_crear_otro_usuario(cliente, sesion_maker):
    await cliente.post(REGISTRO, json=CUERPO)

    respuesta = await cliente.post(REGISTRO, json={**CUERPO, "email": "otro@finca.co"})

    assert respuesta.status_code == 409
    async with sesion_maker() as sesion:
        assert (await sesion.execute(text("SELECT count(*) FROM identidad.usuarios"))).scalar_one() == 1
