import numpy as np
import pytest

from surco_ml import catalogo
from surco_ml.features import construir
from surco_ml.oraculo import etiquetas
from surco_ml.series import COLUMNAS, Serie

ARREGLOS = catalogo.a_arreglos(catalogo.cargar())


def _serie(anios=(1981, 1992), semilla=7) -> Serie:
    fechas = np.arange(np.datetime64(f'{anios[0]}-01-01'), np.datetime64(f'{anios[1] + 1}-01-01'))
    n = len(fechas)
    rng = np.random.default_rng(semilla)
    doy = np.arange(n) % 365
    v = {
        't': 22 + 2 * np.sin(2 * np.pi * doy / 365) + rng.normal(0, 1, n),
        'lluvia': np.where(rng.random(n) < 0.4, rng.gamma(2, 5, n), 0.0),
        'hr': rng.uniform(60, 90, n), 'viento': rng.uniform(0.5, 3, n),
        'radiacion': rng.uniform(12, 22, n), 'et0': rng.uniform(2.5, 5, n),
        'sm_raiz': np.where(np.arange(n) > n - 900, rng.uniform(0.2, 0.4, n), np.nan),
        'sm_superficie': np.where(np.arange(n) > n - 900, rng.uniform(0.2, 0.4, n), np.nan),
        'imerg': rng.gamma(1, 4, n),
    }
    v['tmax'] = v['t'] + 5
    v['tmin'] = v['t'] - 6
    v['lluvia_power'] = v['lluvia'] * 1.1
    assert set(v) == set(COLUMNAS)
    enso = [{'year': a, 'month': m, 'oni': float(np.sin(a + m / 12))} for a in range(1980, 1994) for m in range(1, 13)]
    valores = {'sand': 40.0, 'silt': 35.0, 'clay': 25.0, 'soc': 15.0, 'cfvo': 5.0}
    capas = {f'{a}-{b}cm': {'top_cm': a, 'bottom_cm': b, 'properties': {p: {'Q0.5': x} for p, x in valores.items()}}
             for a, b in ((0, 5), (5, 15), (15, 30), (30, 60), (60, 100), (100, 200))}
    suelo = {'layers': capas,
             'summary': {t: {p: {'Q0.5': 20.0, 'rel_uncertainty': 0.5} for p in construir.PROPIEDADES_SUELO}
                         for t in construir.TRAMOS_SUELO}}
    return Serie('p_test', 2.5, -75.5, 900.0, 1500.0, fechas, v, suelo, enso)


def test_ninguna_feature_usa_el_futuro_del_anio_de_siembra():
    serie = _serie()
    siembras = etiquetas.fechas_siembra(serie)
    base = construir.construir(serie, siembras)

    for k in (100, 157, 230):  # tres siembras de años y meses distintos (12 años × 24 = 288 filas)
        s, anio = siembras['idx'][k], siembras['anio'][k]
        alterada = _serie()
        fin = min(s + 400, len(alterada.fechas))
        for var in alterada.v:
            alterada.v[var] = alterada.v[var].copy()
            alterada.v[var][s:fin] = alterada.v[var][s:fin] * 3 + 50   # clima absurdo desde la siembra
        nuevo = construir.construir(alterada, siembras)
        # Otras filas sí pueden cambiar (su climatología usa este año), pero la fila k nunca:
        # sus ventanas terminan antes de la siembra y su climatología usa solo los demás años.
        for nombre in base:
            a, b = base[nombre][k], nuevo[nombre][k]
            assert (np.isnan(a) and np.isnan(b)) or a == pytest.approx(b), f'{nombre} usa datos del ciclo (año {anio})'


def test_ventanas_terminan_el_dia_antes_de_la_siembra():
    serie = _serie()
    s = np.array([400])
    f = construir.clima_reciente(serie.v, s)
    assert f['f_lluvia_30'][0] == pytest.approx(serie.v['lluvia'][370:400].sum())
    assert f['f_tmax_max_90'][0] == pytest.approx(serie.v['tmax'][310:400].max())


def test_smap_e_imerg_tienen_mascara_antes_de_la_mision():
    serie = _serie()
    siembras = etiquetas.fechas_siembra(serie)
    f = construir.satelite(serie.v, siembras['idx'])
    assert np.isnan(f['f_sm_raiz'][0]) and f['f_smap_disponible'][0] == 0
    assert f['f_smap_disponible'][-1] == 1


def test_enso_usa_el_ultimo_trimestre_completo():
    serie = _serie()
    f = construir.enso(serie, np.array([1990]), np.array([5]))
    # Siembra en mayo: el último trimestre completo es FMA, centrado en marzo
    assert f['f_oni'][0] == pytest.approx(np.sin(1990 + 3 / 12))


def test_etiquetas_y_linea_base_de_un_punto():
    serie = _serie()
    e = etiquetas.etiquetar(serie, ARREGLOS)
    s, c = e['puntaje'].shape
    assert c == 44 and s == 12 * 24
    validos = np.isfinite(e['puntaje'])
    assert validos.mean() > 0.8                       # solo las últimas siembras no completan el ciclo
    assert np.isfinite(e['puntaje_clim'][validos]).all()
    assert ((e['puntaje'][validos] >= 0) & (e['puntaje'][validos] <= 1)).all()
    frec = e['exito_frec_clim'][validos]
    assert ((frec >= 0) & (frec <= 1)).all()
