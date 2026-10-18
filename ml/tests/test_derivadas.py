from datetime import date, timedelta

import pytest

from datos_tierra import derivadas


def test_presion_vapor_saturacion_tabla_fao56():
    # FAO-56, tabla 2.3: e°(20 °C) = 2,338 kPa
    assert derivadas.presion_vapor_saturacion_kpa(20) == pytest.approx(2.338, abs=0.001)


def test_radiacion_extraterrestre_ejemplo_8_fao56():
    # 3 de septiembre (día 246), 20° S -> Ra = 32,2 MJ/m²/día
    assert derivadas.radiacion_extraterrestre_mj(-20, 246) == pytest.approx(32.2, abs=0.1)


def test_et0_penman_monteith_ejemplo_18_fao56():
    # Uccle (Bruselas), 6 de julio: ET0 = 3,9 mm/día
    et0 = derivadas.et0_penman_monteith_mm(
        tmax=21.5, tmin=12.3, rs=22.07, u2=2.078, ea=1.409, z_m=100, lat=50.80, dia_del_anio=187
    )
    assert et0 == pytest.approx(3.9, abs=0.1)


def test_hargreaves_en_rango_razonable_para_el_valle():
    et0 = derivadas.et0_hargreaves_mm(tmax=34, tmin=22, lat=3.2, dia_del_anio=220)
    assert 4 < et0 < 7


def test_correccion_temperatura_villavieja():
    # Celda POWER a 1403 m, lote a 385 m (SRTM) -> +6,6 °C
    assert derivadas.correccion_temperatura_c(1402.97, 385) == pytest.approx(6.62, abs=0.01)


def _fila(**valores):
    base = {'date': '2024-08-07', 'power_t2m': 20.0, 'power_t2m_max': 26.0, 'power_t2m_min': 16.0,
            'power_t2mdew': 15.0, 'power_allsky_sfc_sw_dwn': 21.0, 'power_ws2m': 2.4,
            'power_prectotcorr': 0.3, 'imerg_precip_mm': None}
    return {**base, **valores}


def test_agregar_derivadas_corrige_y_calcula_penman_monteith():
    fila = _fila()
    derivadas.agregar_derivadas(fila, correccion_c=6.62, z_m=385, lat=3.22)
    assert fila['derived_t2m_max_corr'] == pytest.approx(32.62)
    assert fila['derived_et0_method'] == 'penman_monteith'
    assert fila['derived_et0_mm'] == fila['derived_et0_pm_mm'] > 0
    assert fila['derived_precip_source'] == 'power'


def test_sin_radiacion_usa_hargreaves_y_imerg_tiene_prioridad():
    fila = _fila(power_allsky_sfc_sw_dwn=None, imerg_precip_mm=4.2)
    derivadas.agregar_derivadas(fila, correccion_c=0, z_m=385, lat=3.22)
    assert fila['derived_et0_pm_mm'] is None
    assert fila['derived_et0_method'] == 'hargreaves'
    assert (fila['derived_precip_mm'], fila['derived_precip_source']) == (4.2, 'imerg')


def test_climatologia_excluye_anio_y_cubre_365_dias():
    filas, dia = [], date(1991, 1, 1)
    while dia <= date(1993, 12, 31):
        filas.append({'date': dia.isoformat(), 'power_prectotcorr': 10.0 if dia.year == 1992 else 0.0})
        dia += timedelta(days=1)
    clima = derivadas.climatologia_diaria(filas, 1991, 1993, variables=['power_prectotcorr'], excluir_anio=1992)
    assert len(clima) == 365
    assert clima[100]['power_prectotcorr_mean'] == 0.0
    assert clima[100]['power_prectotcorr_wet_day_prob'] == 0.0
