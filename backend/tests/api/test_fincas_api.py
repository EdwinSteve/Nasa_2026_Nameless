from uuid import uuid4

import httpx
import pytest

from app.api import app
from app.modules.fincas.api.dependencies import (
    get_crear_finca,
    get_crear_lote,
    get_guardar_preferencias,
    get_obtener_lote,
)
from app.modules.identidad.api.dependencies import usuario_actual
from app.modules.identidad.domain.entity import Role, User, UserStatus
from app.modules.identidad.domain.values import Phone
from tests.unit.fincas_fakes import FORTALECILLAS, NEIVA, POLIGONO
from tests.unit.test_casos_fincas import Entorno

USUARIO = User(phone=Phone("+573001234567"), email=None, password_hash="x", role=Role.PRODUCTOR, status=UserStatus.ACTIVE)
FINCA = {"nombre": "La Esperanza", "municipio": NEIVA, "corregimiento": FORTALECILLAS, "vereda": ""}
LOTE = {"nombre": "La Vega", "poligono": POLIGONO, "tiene_riego": True, "tipo_riego": "goteo", "cultivo_anterior": "maiz"}


@pytest.fixture
def entorno():
    e = Entorno()
    app.dependency_overrides.update({
        usuario_actual: lambda: USUARIO,
        get_crear_finca: lambda: e.crear_finca,
        get_crear_lote: lambda: e.crear_lote,
        get_obtener_lote: lambda: e.obtener_lote,
        get_guardar_preferencias: lambda: e.guardar,
    })
    yield e
    app.dependency_overrides.clear()


@pytest.fixture
async def cliente(entorno):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_flujo_finca_lote_preferencias(cliente, entorno):
    finca = await cliente.post("/api/v1/fincas", json=FINCA)
    assert finca.status_code == 201, finca.text
    assert set(finca.json()) == {"id", "nombre"}

    lote = await cliente.post(f"/api/v1/fincas/{finca.json()['id']}/lotes", json=LOTE)
    assert lote.status_code == 201, lote.text
    assert lote.json()["area_ha"] == pytest.approx(32.7395, rel=1e-4)
    assert lote.json()["centroide"] == pytest.approx({"lat": 2.98886, "lon": -75.29124}, abs=1e-4)

    detalle = await cliente.get(f"/api/v1/lotes/{lote.json()['id']}")
    assert detalle.status_code == 200
    assert detalle.json()["municipio_nombre"] == "Neiva"
    assert detalle.json()["poligono"] == POLIGONO

    pref = await cliente.put(
        "/api/v1/usuarios/me/preferencias",
        json={"orden": ["ahorro_agua", "ganar_mas", "cuidar_suelo", "arriesgar_menos"]},
    )
    assert pref.status_code == 204
    assert entorno.preferencias.por_usuario[USUARIO.id].orden[0].value == "ahorro_agua"


async def test_vereda_vacia_se_guarda_como_null(cliente, entorno):
    respuesta = await cliente.post("/api/v1/fincas", json=FINCA)

    assert entorno.fincas.por_id[next(iter(entorno.fincas.por_id))].vereda is None
    assert respuesta.status_code == 201


async def test_codigos_divipola_mal_formados_responden_422(cliente):
    respuesta = await cliente.post("/api/v1/fincas", json={**FINCA, "municipio": "Neiva"})

    assert respuesta.status_code == 422
    assert respuesta.json()["details"][0]["field"] == "body.municipio"


async def test_poligono_invalido_responde_422_con_mensaje_para_el_productor(cliente):
    finca = (await cliente.post("/api/v1/fincas", json=FINCA)).json()
    abierto = {"type": "Polygon", "coordinates": [POLIGONO["coordinates"][0][:-1]]}

    respuesta = await cliente.post(f"/api/v1/fincas/{finca['id']}/lotes", json={**LOTE, "poligono": abierto})

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "LOTE_POLIGONO_INVALIDO"
    assert "cerrarse" in respuesta.json()["message"]


async def test_finca_inexistente_responde_404(cliente):
    respuesta = await cliente.post(f"/api/v1/fincas/{uuid4()}/lotes", json=LOTE)

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "FINCA_NO_ENCONTRADA"


async def test_sin_sesion_responde_401():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as cliente:
        respuesta = await cliente.post("/api/v1/fincas", json=FINCA)

    assert respuesta.status_code == 401
    assert respuesta.json()["code"] == "AUTH_NO_AUTENTICADO"
