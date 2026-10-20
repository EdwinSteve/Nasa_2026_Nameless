"""Flujo del wizard contra PostgreSQL: registro → finca → lote → preferencias."""

import httpx
import pytest
from sqlalchemy import text

from tests.integration.test_registro_postgres import CUERPO as REGISTRO
from tests.unit.fincas_fakes import FORTALECILLAS, NEIVA, POLIGONO

FINCA = {"nombre": "La Esperanza", "municipio": NEIVA, "corregimiento": FORTALECILLAS, "vereda": "El Vergel"}
LOTE = {"nombre": "La Vega", "poligono": POLIGONO, "tiene_riego": False, "tipo_riego": None, "cultivo_anterior": None}


@pytest.fixture
async def cliente(app_db):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app_db), base_url="http://test") as c:
        yield c


async def registrar(cliente, celular: str) -> dict:
    respuesta = await cliente.post("/api/v1/auth/registro", json={**REGISTRO, "phone": celular})
    assert respuesta.status_code == 201, respuesta.text
    return {"Authorization": f"Bearer {respuesta.json()['tokens']['access_token']}"}


async def test_flujo_completo_del_wizard(cliente, sesion_maker):
    auth = await registrar(cliente, "3001234567")

    finca = await cliente.post("/api/v1/fincas", json=FINCA, headers=auth)
    assert finca.status_code == 201, finca.text
    lote = await cliente.post(f"/api/v1/fincas/{finca.json()['id']}/lotes", json=LOTE, headers=auth)
    assert lote.status_code == 201, lote.text
    orden = ["arriesgar_menos", "ahorro_agua", "ganar_mas", "cuidar_suelo"]
    for _ in range(2):  # guardar dos veces reemplaza, no duplica
        pref = await cliente.put("/api/v1/usuarios/me/preferencias", json={"orden": orden}, headers=auth)
        assert pref.status_code == 204

    detalle = await cliente.get(f"/api/v1/lotes/{lote.json()['id']}", headers=auth)
    assert detalle.status_code == 200
    assert (detalle.json()["municipio_nombre"], detalle.json()["corregimiento_nombre"]) == ("Neiva", "Fortalecillas")
    assert detalle.json()["poligono"] == POLIGONO

    async with sesion_maker() as sesion:
        fila = (await sesion.execute(text(
            "SELECT l.area_ha, l.centroide_lat, f.vereda FROM fincas.lotes l JOIN fincas.fincas f ON f.id = l.finca_id"
        ))).mappings().one()
        guardado = (await sesion.execute(text("SELECT orden FROM fincas.preferencias_productor"))).scalars().all()
    assert float(fila["area_ha"]) == pytest.approx(32.7395, rel=1e-4)
    assert fila["vereda"] == "El Vergel"
    assert guardado == [orden]


async def test_otro_productor_no_ve_ni_usa_lo_ajeno(cliente):
    dueno = await registrar(cliente, "3001234567")
    intruso = await registrar(cliente, "3109876543")
    finca = (await cliente.post("/api/v1/fincas", json=FINCA, headers=dueno)).json()
    lote = (await cliente.post(f"/api/v1/fincas/{finca['id']}/lotes", json=LOTE, headers=dueno)).json()

    ajena = await cliente.post(f"/api/v1/fincas/{finca['id']}/lotes", json=LOTE, headers=intruso)
    ver = await cliente.get(f"/api/v1/lotes/{lote['id']}", headers=intruso)

    assert ajena.status_code == 404 and ver.status_code == 404
