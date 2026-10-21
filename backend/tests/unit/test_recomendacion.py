from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.modules.recomendacion.application.casos import (
    CalcularRecomendacion,
    ConsultarRecomendacion,
    SolicitarRecomendacion,
)
from app.modules.recomendacion.domain.entity import EstadoRecomendacion, Recomendacion
from app.modules.recomendacion.domain.errors import (
    FechaSiembraInvalida,
    LoteSinAcceso,
    ModeloNoDisponible,
    RecomendacionNoEncontrada,
)
from tests.unit.diagnostico_fakes import AHORA, DUENO, RelojFalso
from tests.unit.recomendacion_fakes import (
    LOTE_R,
    RESULTADO,
    ULTIMA,
    LotesFalsos,
    ModeloFalso,
    RecomendacionesFalsas,
    UnitOfWorkFalso,
    fabrica,
)


def _solicitar(repo, modelo):
    return SolicitarRecomendacion(lotes=LotesFalsos(), recomendaciones=repo, modelo=modelo, uow=UnitOfWorkFalso())


async def test_sin_fecha_usa_la_mas_reciente_con_datos():
    rec, lote = await _solicitar(RecomendacionesFalsas(), ModeloFalso()).ejecutar(DUENO, LOTE_R.lote_id, None)

    assert rec.fecha_siembra == ULTIMA and rec.estado is EstadoRecomendacion.EN_PROCESO
    assert lote == LOTE_R


@pytest.mark.parametrize(
    "fecha, mensaje",
    [(date(2026, 9, 10), "día 1 o 16"), (date(2026, 10, 16), "Todavía no hay datos"), (date(1981, 6, 1), "1982")],
)
async def test_fechas_invalidas(fecha, mensaje):
    with pytest.raises(FechaSiembraInvalida, match=mensaje):
        await _solicitar(RecomendacionesFalsas(), ModeloFalso()).ejecutar(DUENO, LOTE_R.lote_id, fecha)


async def test_sin_modelo_no_crea_nada():
    repo = RecomendacionesFalsas()

    with pytest.raises(ModeloNoDisponible, match="modelo_a_puntaje.ubj"):
        await _solicitar(repo, ModeloFalso(motivo="Faltan modelo_a_puntaje.ubj")).ejecutar(DUENO, LOTE_R.lote_id, None)
    assert not repo.por_id


async def test_lote_ajeno():
    with pytest.raises(LoteSinAcceso):
        await _solicitar(RecomendacionesFalsas(), ModeloFalso()).ejecutar(uuid4(), LOTE_R.lote_id, None)


async def test_calcular_guarda_el_resultado_o_el_error():
    repo = RecomendacionesFalsas()
    modelo = ModeloFalso()
    rec, lote = await _solicitar(repo, modelo).ejecutar(DUENO, LOTE_R.lote_id, None)

    await CalcularRecomendacion(modelo=modelo, fabrica=fabrica(repo), reloj=RelojFalso()).ejecutar(rec.id, lote, rec.fecha_siembra)

    guardada = repo.por_id[rec.id]
    assert guardada.estado is EstadoRecomendacion.LISTA and guardada.resultado == RESULTADO
    assert modelo.pedidos == [(LOTE_R.lat, LOTE_R.lon, ULTIMA)]   # el punto medio del lote

    otra, _ = await _solicitar(repo, modelo).ejecutar(DUENO, LOTE_R.lote_id, None)
    await CalcularRecomendacion(modelo=ModeloFalso(falla=True), fabrica=fabrica(repo), reloj=RelojFalso()).ejecutar(otra.id, lote, ULTIMA)
    assert repo.por_id[otra.id].estado is EstadoRecomendacion.FALLIDA
    assert "Earth Engine" in repo.por_id[otra.id].error


async def test_consultar_marca_colgada_y_valida_el_lote():
    repo = RecomendacionesFalsas()
    rec = await repo.crear(Recomendacion(lote_id=LOTE_R.lote_id, fecha_siembra=ULTIMA))
    consultar = ConsultarRecomendacion(lotes=LotesFalsos(), recomendaciones=repo, reloj=RelojFalso(AHORA + timedelta(hours=1)))

    vista, _ = await consultar.ejecutar(DUENO, LOTE_R.lote_id, rec.id)

    assert vista.estado is EstadoRecomendacion.FALLIDA and "interrumpió" in vista.error
    ajena = await repo.crear(Recomendacion(lote_id=uuid4(), fecha_siembra=ULTIMA))
    with pytest.raises(RecomendacionNoEncontrada):
        await consultar.ejecutar(DUENO, LOTE_R.lote_id, ajena.id)
