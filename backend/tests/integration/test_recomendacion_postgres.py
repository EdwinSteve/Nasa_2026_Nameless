"""Recomendación contra PostgreSQL con un modelo falso (sin red ni archivos .ubj)."""
import httpx
import pytest
from sqlalchemy import text

from app.modules.recomendacion.api.dependencies import get_calcular, get_modelo
from app.modules.recomendacion.application.casos import CalcularRecomendacion
from app.modules.recomendacion.infrastructure.repositories import RelojSistema, fabrica_recomendaciones
from tests.integration.test_fincas_postgres import FINCA, LOTE, registrar
from tests.unit.recomendacion_fakes import ModeloFalso


@pytest.fixture
async def cliente(app_db, sesion_maker):
    modelo = ModeloFalso()
    app_db.dependency_overrides[get_modelo] = lambda: modelo
    app_db.dependency_overrides[get_calcular] = lambda: CalcularRecomendacion(
        modelo=modelo, fabrica=fabrica_recomendaciones(sesion_maker), reloj=RelojSistema()
    )
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app_db), base_url="http://test") as c:
        yield c


async def test_recomendacion_se_guarda_y_se_consulta(cliente, sesion_maker):
    auth = await registrar(cliente, "3001234567")
    finca = (await cliente.post("/api/v1/fincas", json=FINCA, headers=auth)).json()
    lote = (await cliente.post(f"/api/v1/fincas/{finca['id']}/lotes", json=LOTE, headers=auth)).json()

    pedido = await cliente.post(f"/api/v1/lotes/{lote['id']}/recomendaciones", json={}, headers=auth)
    assert pedido.status_code == 202, pedido.text
    r = await cliente.get(f"/api/v1/lotes/{lote['id']}/recomendaciones/{pedido.json()['recomendacion_id']}", headers=auth)

    assert r.status_code == 200 and r.json()["estado"] == "lista"
    assert r.json()["cultivos"][0]["id"] == "maiz"
    async with sesion_maker() as sesion:
        fila = (await sesion.execute(text(
            "SELECT estado, fecha_siembra, resultado->>'corrida' AS corrida FROM recomendacion.recomendaciones"
        ))).mappings().one()
    assert fila["estado"] == "lista" and fila["corrida"] == "tiempo"
    assert fila["fecha_siembra"].isoformat() == pedido.json()["fecha_siembra"]


async def test_otro_productor_no_ve_la_recomendacion(cliente):
    dueno = await registrar(cliente, "3001234567")
    intruso = await registrar(cliente, "3109876543")
    finca = (await cliente.post("/api/v1/fincas", json=FINCA, headers=dueno)).json()
    lote = (await cliente.post(f"/api/v1/fincas/{finca['id']}/lotes", json=LOTE, headers=dueno)).json()
    rid = (await cliente.post(f"/api/v1/lotes/{lote['id']}/recomendaciones", json={}, headers=dueno)).json()["recomendacion_id"]

    assert (await cliente.get(f"/api/v1/lotes/{lote['id']}/recomendaciones/{rid}", headers=intruso)).status_code == 404
    assert (await cliente.post(f"/api/v1/lotes/{lote['id']}/recomendaciones", json={}, headers=intruso)).status_code == 404
