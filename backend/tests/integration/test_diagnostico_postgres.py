"""Diagnóstico contra PostgreSQL con un proveedor de datos falso (sin red)."""

import httpx
import pytest
from sqlalchemy import text

from app.modules.diagnostico.api.dependencies import get_ejecutar_diagnostico
from app.modules.diagnostico.application.casos import EjecutarDiagnostico
from app.modules.diagnostico.infrastructure.repositories import RelojSistema, fabrica_tareas
from tests.integration.test_fincas_postgres import FINCA, LOTE, registrar
from tests.unit.diagnostico_fakes import ProveedorFalso


@pytest.fixture
async def cliente(app_db, sesion_maker):
    app_db.dependency_overrides[get_ejecutar_diagnostico] = lambda: EjecutarDiagnostico(
        proveedor=ProveedorFalso(fallan=("humedad",)), fabrica=fabrica_tareas(sesion_maker), reloj=RelojSistema()
    )
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app_db), base_url="http://test") as c:
        yield c


async def test_diagnostico_guarda_los_cuatro_pasos_en_paralelo(cliente, sesion_maker):
    auth = await registrar(cliente, "3001234567")
    finca = (await cliente.post("/api/v1/fincas", json=FINCA, headers=auth)).json()
    lote = (await cliente.post(f"/api/v1/fincas/{finca['id']}/lotes", json=LOTE, headers=auth)).json()

    inicio = await cliente.post(f"/api/v1/lotes/{lote['id']}/diagnostico", headers=auth)
    assert inicio.status_code == 202, inicio.text
    tarea_id = inicio.json()["tarea_id"]
    respuesta = await cliente.get(f"/api/v1/lotes/{lote['id']}/diagnostico/{tarea_id}", headers=auth)

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "lista"
    assert [p["estado"] for p in cuerpo["pasos"]] == ["lista", "fallida", "lista", "lista"]
    async with sesion_maker() as sesion:
        filas = (await sesion.execute(text(
            "SELECT codigo, estado, iniciado_en IS NOT NULL AS inicio, terminado_en IS NOT NULL AS fin, datos "
            "FROM diagnostico.pasos ORDER BY orden"
        ))).mappings().all()
    assert all(f["inicio"] and f["fin"] for f in filas)
    assert filas[0]["datos"] == {"paso": "clima"}


async def test_otro_productor_no_ve_el_diagnostico(cliente):
    dueno = await registrar(cliente, "3001234567")
    intruso = await registrar(cliente, "3109876543")
    finca = (await cliente.post("/api/v1/fincas", json=FINCA, headers=dueno)).json()
    lote = (await cliente.post(f"/api/v1/fincas/{finca['id']}/lotes", json=LOTE, headers=dueno)).json()
    tarea_id = (await cliente.post(f"/api/v1/lotes/{lote['id']}/diagnostico", headers=dueno)).json()["tarea_id"]

    respuesta = await cliente.get(f"/api/v1/lotes/{lote['id']}/diagnostico/{tarea_id}", headers=intruso)

    assert respuesta.status_code == 404
