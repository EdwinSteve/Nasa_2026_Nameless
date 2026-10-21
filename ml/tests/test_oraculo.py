import importlib.util

import numpy as np
import pytest

from surco_ml import catalogo
from surco_ml.oraculo import simulador
from surco_ml.rutas import MOTOR_AGRONOMICO, RAIZ
from surco_ml import suelo_motor  # noqa: F401  (agrega el motor agronómico al path)
from formulas import calculate_daily_depletion, calculate_ks

_spec = importlib.util.spec_from_file_location(
    'ejemplo_modelo', RAIZ / 'data/catalogo_cultivos_mongodb/scripts/ejemplo_modelo.py')
ejemplo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ejemplo)

CULTIVOS = catalogo.cargar()
ARREGLOS = catalogo.a_arreglos(CULTIVOS)
MAIZ = ARREGLOS.ids.index('maiz')


def _serie_neiva_maiz():
    """La misma serie sintética de ejemplo_modelo.py: una semilla distinta por fase del maíz."""
    maiz = next(c for c in CULTIVOS if c['_id'] == 'maiz')
    dias, fases = [], sorted(maiz['fases'], key=lambda f: f['orden'])
    for fase in fases:
        dias += ejemplo.serie_sintetica(catalogo.duracion_fase(fase), semilla=fase['orden'])
    v = {
        't': np.array([d['T2M'] for d in dias]), 'tmax': np.array([d['T2M_MAX'] for d in dias]),
        'lluvia': np.array([d['PRECTOTCORR'] for d in dias]), 'hr': np.array([d['RH2M'] for d in dias]),
        'viento': np.array([d['WS2M'] for d in dias]), 'et0': np.full(len(dias), 5.0),
    }
    return v, dias, fases


def test_cada_fase_puntua_igual_que_ejemplo_modelo():
    v, dias, fases = _serie_neiva_maiz()
    i0 = 0
    for j, fase in enumerate(fases):
        i1 = i0 + catalogo.duracion_fase(fase)
        esperado = ejemplo.evaluar_fase(fase, dias[i0:i1])['fase']
        obtenido, _ = simulador.puntaje_fase(
            v['t'], v['tmax'], v['lluvia'], v['hr'], v['viento'], i0, i1, ARREGLOS.temp[MAIZ, j],
            ARREGLOS.lluvia[MAIZ, j], ARREGLOS.hr[MAIZ, j], ARREGLOS.viento_max[MAIZ, j], ARREGLOS.temp_critica[MAIZ, j])
        assert obtenido == pytest.approx(esperado, abs=1e-3), fase['codigo']
        i0 = i1


def test_maiz_en_neiva_sale_mal_en_floracion_sin_riego():
    v, _, fases = _serie_neiva_maiz()
    taw = np.full(len(ARREGLOS.ids), 100.0)
    r = simulador.simular(v, np.array([0]), ARREGLOS, taw)

    floracion = [f['codigo'] for f in fases].index('floracion')
    assert r['fase_critica'][0, MAIZ] == floracion
    assert r['exito'][0, MAIZ] == 0.0          # floración bajo el umbral de falla crítica
    assert r['puntaje'][0, MAIZ] < 0.6


def _balance_de_referencia(lluvia, et0, kc, p, taw, dr0):
    """Balance en secano con las funciones del motor agronómico, día a día."""
    dr, estres = dr0, 0
    for llu, e, k, pp in zip(lluvia, et0, kc, p):
        ks = calculate_ks(dr=dr, taw=taw, p=pp)
        estres += ks < 1.0
        dr = calculate_daily_depletion(previous_dr=dr, effective_rainfall=llu, irrigation=0.0, etc=ks * k * e, taw=taw)
    return estres


def test_balance_hidrico_igual_al_del_motor_agronomico():
    rng = np.random.default_rng(7)
    n = 400
    v = {'t': np.full(n, 25.0), 'tmax': np.full(n, 30.0), 'hr': np.full(n, 70.0), 'viento': np.full(n, 1.5),
         'lluvia': np.where(rng.random(n) < 0.3, rng.gamma(2, 6, n), 0.0), 'et0': rng.uniform(3, 6, n)}
    taw = np.full(len(ARREGLOS.ids), 120.0)
    s = simulador.DIAS_ARRANQUE + 10
    r = simulador.simular(v, np.array([s]), ARREGLOS, taw)

    # Referencia: arranque con el Kc inicial y luego las fases del maíz
    dur = ARREGLOS.duracion[MAIZ, :ARREGLOS.n_fases[MAIZ]]
    kc_dia = np.repeat(ARREGLOS.kc[MAIZ, :len(dur)], dur)
    p_dia = np.repeat(ARREGLOS.p[MAIZ, :len(dur)], dur)
    a = s - simulador.DIAS_ARRANQUE
    dr = simulador.AGOTAMIENTO_ARRANQUE * 120.0
    for i in range(a, s):
        ks = calculate_ks(dr=dr, taw=120.0, p=ARREGLOS.p[MAIZ, 0])
        dr = calculate_daily_depletion(previous_dr=dr, effective_rainfall=v['lluvia'][i], irrigation=0.0,
                                       etc=ks * ARREGLOS.kc[MAIZ, 0] * v['et0'][i], taw=120.0)
    fin = s + len(kc_dia)
    esperado = _balance_de_referencia(v['lluvia'][s:fin], v['et0'][s:fin], kc_dia, p_dia, 120.0, dr)
    assert r['dias_estres'][0, MAIZ] == esperado


def test_riego_repone_lo_que_falta_sin_lluvia():
    n = 300
    v = {'t': np.full(n, 25.0), 'tmax': np.full(n, 30.0), 'hr': np.full(n, 70.0), 'viento': np.full(n, 1.5),
         'lluvia': np.zeros(n), 'et0': np.full(n, 5.0)}
    taw = np.full(len(ARREGLOS.ids), 100.0)
    r = simulador.simular(v, np.array([0]), ARREGLOS, taw)

    # Balance de masa sin lluvia: riego = ETc + agotamiento inicial − agotamiento final (0 ≤ final ≤ TAW)
    etc_total = (ARREGLOS.kc[MAIZ, :5] * 5.0 * ARREGLOS.duracion[MAIZ, :5]).sum()
    inicial = simulador.AGOTAMIENTO_ARRANQUE * 100.0
    final = etc_total + inicial - r['riego_mm'][0, MAIZ]
    assert 0.0 <= final <= 100.0
    assert r['dias_estres'][0, MAIZ] > 0


def test_cultivo_sin_kc_no_tiene_etiquetas_de_agua():
    v, _, _ = _serie_neiva_maiz()
    v = {k: np.concatenate([x] * 4) for k, x in v.items()}
    mango = ARREGLOS.ids.index('mango')
    assert not ARREGLOS.tiene_agua[mango]
    r = simulador.simular(v, np.array([0]), ARREGLOS, np.full(len(ARREGLOS.ids), 100.0))
    assert np.isnan(r['riego_mm'][0, mango]) and np.isfinite(r['puntaje'][0, mango])


def test_arroz_de_riego_no_depende_de_la_lluvia():
    v, _, _ = _serie_neiva_maiz()
    v = {k: np.concatenate([x] * 2) for k, x in v.items()}
    seco = {**v, 'lluvia': np.zeros_like(v['lluvia'])}
    taw = np.full(len(ARREGLOS.ids), 100.0)
    riego, secano = ARREGLOS.ids.index('arroz_riego'), ARREGLOS.ids.index('arroz_secano')
    con_lluvia = simulador.simular(v, np.array([0]), ARREGLOS, taw)
    sin_lluvia = simulador.simular(seco, np.array([0]), ARREGLOS, taw)
    assert sin_lluvia['puntaje'][0, riego] == pytest.approx(con_lluvia['puntaje'][0, riego])
    assert sin_lluvia['riego_mm'][0, riego] > con_lluvia['riego_mm'][0, riego]
    assert sin_lluvia['puntaje'][0, secano] < con_lluvia['puntaje'][0, secano]


def test_siembra_sin_ciclo_completo_queda_en_nan():
    v, _, _ = _serie_neiva_maiz()
    r = simulador.simular(v, np.array([len(v['t']) - 10]), ARREGLOS, np.full(len(ARREGLOS.ids), 100.0))
    assert np.isnan(r['puntaje']).all()


def test_catalogo_completo_en_arreglos():
    assert len(ARREGLOS.ids) == 44
    assert (ARREGLOS.duracion.sum(axis=1) > 0).all()
    assert np.isfinite(ARREGLOS.temp[:, 0]).all() and np.isfinite(ARREGLOS.lluvia[:, 0]).all()
    assert ARREGLOS.tiene_agua.sum() == 37   # los 7 sin Kc ni p: ñame y 6 frutales
