import httpx
import pytest

from app.api import app
from app.modules.identidad.api.dependencies import usuario_actual
from app.modules.recomendacion.api.dependencies import get_calcular, get_consultar, get_modelo, get_solicitar
from app.modules.recomendacion.application.casos import (
    CalcularRecomendacion,
    ConsultarRecomendacion,
    SolicitarRecomendacion,
)
from tests.api.test_diagnostico_api import USUARIO
from tests.unit.diagnostico_fakes import RelojFalso
from tests.unit.recomendacion_fakes import (
    LOTE_R,
    LotesFalsos,
    ModeloFalso,
    RecomendacionesFalsas,
    UnitOfWorkFalso,
    fabrica,
)

BASE = f"/api/v1/lotes/{LOTE_R.lote_id}/recomendaciones"


def _montar(modelo: ModeloFalso):
    repo, lotes = RecomendacionesFalsas(), LotesFalsos()
    app.dependency_overrides.update({
        usuario_actual: lambda: USUARIO,
        get_modelo: lambda: modelo,
        get_solicitar: lambda: SolicitarRecomendacion(lotes=lotes, recomendaciones=repo, modelo=modelo, uow=UnitOfWorkFalso()),
        get_consultar: lambda: ConsultarRecomendacion(lotes=lotes, recomendaciones=repo, reloj=RelojFalso()),
        get_calcular: lambda: CalcularRecomendacion(modelo=modelo, fabrica=fabrica(repo), reloj=RelojFalso()),
    })


@pytest.fixture
async def cliente():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


async def test_recomendacion_completa_con_ranking_y_descartados(cliente):
    _montar(ModeloFalso())

    pedido = await cliente.post(BASE, json={})
    assert pedido.status_code == 202, pedido.text
    respuesta = await cliente.get(f"{BASE}/{pedido.json()['recomendacion_id']}")

    assert respuesta.status_code == 200
    r = respuesta.json()
    assert r["estado"] == "lista" and r["fecha_siembra"] == "2026-10-01" and r["modelo"] == "tiempo"
    assert [c["id"] for c in r["cultivos"]] == ["maiz", "mango", "frijol"]       # por puntaje; la papa no pasa
    maiz = r["cultivos"][0]
    assert maiz["de_cada_10"] == 8 and maiz["riego_bruto_m3_ha"] == 3400          # 306 mm / 0,9 × 10
    assert r["cultivos"][1]["riego_neto_mm"] is None                              # mango sin Kc en el catálogo
    assert r["descartados"] == [{"id": "papa", "cultivo": "Papa", "motivo": "altitud 464 m fuera de 2000-3500 m"}]
    assert r["contexto"] == {"elevacion_m": 464, "ph_0_30": 5.8, "lluvia_90_dias_mm": 180.5,
                             "temperatura_90_dias_c": 27.1, "oni": 1.8}


async def test_sin_modelo_responde_503_con_el_motivo(cliente):
    _montar(ModeloFalso(motivo="Faltan los archivos del modelo 'tiempo'"))

    pedido = await cliente.post(BASE, json={})
    estado = await cliente.get("/api/v1/recomendaciones/modelo")

    assert pedido.status_code == 503 and pedido.json()["code"] == "RECOMENDACION_MODELO_NO_DISPONIBLE"
    assert estado.json() == {"disponible": False, "corrida": "tiempo", "motivo": "Faltan los archivos del modelo 'tiempo'",
                             "ultima_fecha_siembra": None}


async def test_fecha_invalida_responde_422(cliente):
    _montar(ModeloFalso())

    respuesta = await cliente.post(BASE, json={"fecha_siembra": "2026-09-10"})

    assert respuesta.status_code == 422 and respuesta.json()["code"] == "RECOMENDACION_FECHA_INVALIDA"


async def test_calculo_fallido_se_ve_como_fallida(cliente):
    _montar(ModeloFalso(falla=True))

    rid = (await cliente.post(BASE)).json()["recomendacion_id"]
    r = (await cliente.get(f"{BASE}/{rid}")).json()

    assert r["estado"] == "fallida" and r["cultivos"] == [] and "No pudimos" in r["mensaje"]
