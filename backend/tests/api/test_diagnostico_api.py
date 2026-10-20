from uuid import uuid4

import httpx
import pytest

from app.api import app
from app.modules.diagnostico.api.dependencies import (
    get_consultar_diagnostico,
    get_ejecutar_diagnostico,
    get_iniciar_diagnostico,
)
from app.modules.diagnostico.application.casos import ConsultarDiagnostico, EjecutarDiagnostico, IniciarDiagnostico
from app.modules.identidad.api.dependencies import usuario_actual
from app.modules.identidad.domain.entity import Role, User, UserStatus
from app.modules.identidad.domain.values import Phone
from tests.unit.diagnostico_fakes import (
    DUENO,
    LOTE,
    LotesFalsos,
    ProveedorFalso,
    RelojFalso,
    TareasFalsas,
    UnitOfWorkFalso,
    fabrica,
)

USUARIO = User(phone=Phone("+573001234567"), email=None, password_hash="x", role=Role.PRODUCTOR,
               status=UserStatus.ACTIVE, id=DUENO)
BASE = f"/api/v1/lotes/{LOTE.lote_id}/diagnostico"


@pytest.fixture
async def cliente():
    tareas, lotes = TareasFalsas(), LotesFalsos()
    app.dependency_overrides.update({
        usuario_actual: lambda: USUARIO,
        get_iniciar_diagnostico: lambda: IniciarDiagnostico(lotes=lotes, tareas=tareas, uow=UnitOfWorkFalso()),
        get_consultar_diagnostico: lambda: ConsultarDiagnostico(lotes=lotes, tareas=tareas, reloj=RelojFalso()),
        get_ejecutar_diagnostico: lambda: EjecutarDiagnostico(
            proveedor=ProveedorFalso(fallan=("verdor",)), fabrica=fabrica(tareas), reloj=RelojFalso()
        ),
    })
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


async def test_iniciar_responde_202_y_la_consulta_sigue_el_contrato_de_la_ui(cliente):
    inicio = await cliente.post(BASE)
    assert inicio.status_code == 202
    tarea_id = inicio.json()["tarea_id"]

    # La tarea de fondo ya corrió: el transporte ASGI espera a que termine
    respuesta = await cliente.get(f"{BASE}/{tarea_id}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert set(cuerpo) == {
        "tarea_id", "lote_id", "nombre_lote", "area_ha", "corregimiento_nombre", "municipio_nombre",
        "poligono", "estado", "progreso", "paso_activo_codigo", "mensaje_estado", "pasos",
    }
    assert cuerpo["estado"] == "lista" and cuerpo["progreso"] == 100
    assert (cuerpo["municipio_nombre"], cuerpo["corregimiento_nombre"]) == ("Neiva", "Fortalecillas")
    pasos = {p["codigo"]: p for p in cuerpo["pasos"]}
    assert list(pasos) == ["clima", "humedad", "suelo", "verdor"]
    assert pasos["clima"]["resumen"] == "resumen de clima" and pasos["clima"]["fuente"] == "NASA POWER"
    assert pasos["verdor"]["estado"] == "fallida" and pasos["verdor"]["resumen"] is None
    assert set(pasos["suelo"]) == {"codigo", "nombre", "estado", "progreso", "fuente", "resumen"}


async def test_lote_ajeno_responde_404(cliente):
    respuesta = await cliente.post(f"/api/v1/lotes/{uuid4()}/diagnostico")

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "LOTE_NO_ENCONTRADO"


async def test_tarea_inexistente_responde_404(cliente):
    respuesta = await cliente.get(f"{BASE}/{uuid4()}")

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "DIAGNOSTICO_NO_ENCONTRADO"
