from datetime import date

import numpy as np

from surco_ml import catalogo
from surco_ml.predecir import filtros_duros, siembras_de_la_serie
from surco_ml.series import Serie

LISTA = catalogo.cargar()


def test_filtros_duros_por_altitud_y_ph():
    motivos = dict(zip((c['_id'] for c in LISTA), filtros_duros(LISTA, elevacion=1472, ph=5.3)))
    assert motivos['cafe'] is None
    assert 'altitud' in motivos['arroz_riego'] and 'altitud' in motivos['papa']
    assert 'pH' in dict(zip((c['_id'] for c in LISTA), filtros_duros(LISTA, 500, 3.0)))['maiz']


def test_siembras_llegan_hasta_la_fecha_pedida_aunque_pase_de_2024():
    fechas = np.arange(np.datetime64('1981-01-01'), np.datetime64('2026-01-01'))
    serie = Serie('p', 2.0, -75.0, 500.0, 900.0, fechas, {}, None)
    s = siembras_de_la_serie(serie, date(2025, 3, 1))
    assert s['anio'][-1] == 2025 and s['mes'][-1] == 3 and s['dia'][-1] == 1
    assert len(s['idx']) == 44 * 24 + 5          # 1981-2024 completos + ene-1 a mar-1 de 2025
