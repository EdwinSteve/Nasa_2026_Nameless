"""Orquestación sin red: las fuentes se reemplazan por respuestas falsas."""
import asyncio

import pytest

from datos_tierra import unificar
from datos_tierra.fuentes import power


def _power_falso(inicio, fin):
    dias = [f'{d}'.replace('-', '') for d in unificar._dias(inicio, fin)]
    valores = {
        'T2M': 20.0, 'T2M_MAX': 26.0, 'T2M_MIN': 16.0, 'T2MDEW': 15.0, 'RH2M': 75.0, 'QV2M': 11.0,
        'PRECTOTCORR': 2.0, 'WS2M': 2.4, 'WS2M_MAX': 5.0, 'ALLSKY_SFC_SW_DWN': 21.0,
        'CLRSKY_SFC_SW_DWN': 26.0, 'ALLSKY_SFC_PAR_TOT': 100.0, 'GWETROOT': 0.6, 'GWETTOP': 0.5,
        'GWETPROF': 0.6, 'PS': 96.0, 'EVPTRNS': 3.0, 'TS': 24.0,
    }
    parametro = {p: {d: valores[p] for d in dias} for p in power.PARAMETROS}
    parametro['PRECTOTCORR'][dias[0]] = -999.0
    return {'header': {'fill_value': -999.0}, 'geometry': {'coordinates': [-75.22, 3.22, 1402.97]},
            'properties': {'parameter': parametro}, 'parameters': {}}


@pytest.fixture
def sin_red(monkeypatch):
    async def power_descargar(cliente, lat, lon, inicio, fin):
        return _power_falso(inicio, fin)

    async def dem_elevaciones(cliente, puntos):
        return [385.0]

    async def soil_descargar(cliente, lat, lon):
        raise RuntimeError('SoilGrids caído')

    monkeypatch.setattr(unificar.power, 'descargar', power_descargar)
    monkeypatch.setattr(unificar.dem, 'elevaciones', dem_elevaciones)
    monkeypatch.setattr(unificar.soilgrids, 'descargar', soil_descargar)


def _ejecutar(**kwargs):
    return asyncio.run(unificar.ejecutar(None, 3.22, -75.22, '2024-08-01', '2024-08-10', **kwargs))


def test_corrige_temperatura_con_dem_y_aisla_fuente_caida(sin_red):
    datos = _ejecutar(fuentes=('power', 'dem', 'soilgrids'))
    assert datos['schema_version'] == '2.0'
    assert datos['site']['temperature_correction_c'] == pytest.approx(6.62, abs=0.01)
    assert datos['sources']['soilgrids']['status'] == 'error'
    assert datos['sources']['power']['status'] == 'ok'
    primer_dia = datos['daily'][0]
    assert primer_dia['power_prectotcorr'] is None  # -999 -> None
    assert primer_dia['derived_t2m_max_corr'] == pytest.approx(32.62)
    assert datos['quality']['missing_days']['power_prectotcorr'] == 1


def test_gee_sin_configurar_queda_omitido(sin_red, monkeypatch):
    monkeypatch.delenv('GEE_PROJECT', raising=False)
    datos = _ejecutar(fuentes=('power', 'dem', 'smap', 'imerg'))
    assert datos['sources']['smap']['status'] == 'skipped'
    assert datos['sources']['imerg']['status'] == 'skipped'
    assert all(f['derived_precip_source'] in ('power', None) for f in datos['daily'])


def test_elevacion_del_usuario_evita_el_dem(sin_red):
    datos = _ejecutar(fuentes=('power', 'dem'), elevacion_m=500)
    assert 'dem' not in datos['sources']
    assert datos['site']['elevation_source'] == 'usuario'


def test_fuente_desconocida_falla():
    with pytest.raises(ValueError):
        _ejecutar(fuentes=('power', 'chirps'))
