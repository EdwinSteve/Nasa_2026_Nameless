import asyncio
import gzip
import json

from datos_tierra import __main__ as cli

SUELO_CRUDO = {'properties': {'layers': [{
    'name': 'clay',
    'unit_measure': {'d_factor': 10, 'mapped_units': 'g/kg', 'target_units': '%'},
    'depths': [{'label': '0-5cm', 'range': {'top_depth': 0, 'bottom_depth': 5}, 'values': {'mean': 373, 'Q0.5': 370}}],
}]}}


def _archivo(tmp_path, estado_suelo):
    ruta = tmp_path / 'p0001.json.gz'
    datos = {
        'location': {'lat': 1.82, 'lon': -76.02},
        'sources': {'power': {'status': 'ok'}, 'soilgrids': {'status': estado_suelo}},
        'soil': None,
        'quality': {'alerts': []},
    }
    with gzip.open(ruta, 'wt', encoding='utf-8') as fh:
        json.dump(datos, fh)
    return ruta


def test_completa_el_suelo_si_soilgrids_habia_fallado(tmp_path, monkeypatch):
    async def descargar(cliente, lat, lon):
        return SUELO_CRUDO
    monkeypatch.setattr(cli.soilgrids, 'descargar', descargar)
    ruta = _archivo(tmp_path, 'error')

    assert asyncio.run(cli._completar_suelo(None, ruta)) == 'suelo completado'
    datos = cli._leer(ruta)
    assert datos['sources']['soilgrids']['status'] == 'ok'
    assert datos['soil']['layers']['0-5cm']['properties']['clay']['mean'] == 37.3


def test_completa_el_suelo_si_no_se_habia_pedido(tmp_path, monkeypatch):
    async def descargar(cliente, lat, lon):
        return SUELO_CRUDO
    monkeypatch.setattr(cli.soilgrids, 'descargar', descargar)
    ruta = _archivo(tmp_path, 'ok')
    datos = cli._leer(ruta)
    del datos['sources']['soilgrids']           # descarga hecha con --fuentes sin SoilGrids
    cli._guardar(datos, ruta, comprimir=True)

    assert asyncio.run(cli._completar_suelo(None, ruta)) == 'suelo completado'
    assert cli._leer(ruta)['sources']['soilgrids']['status'] == 'ok'


def test_no_toca_un_archivo_completo(tmp_path, monkeypatch):
    async def descargar(cliente, lat, lon):
        raise AssertionError('no debía pedir el suelo')
    monkeypatch.setattr(cli.soilgrids, 'descargar', descargar)

    assert asyncio.run(cli._completar_suelo(None, _archivo(tmp_path, 'ok'))) == 'ya existe, se salta'


def test_si_soilgrids_sigue_caido_deja_el_archivo_igual(tmp_path, monkeypatch):
    async def descargar(cliente, lat, lon):
        raise TimeoutError
    monkeypatch.setattr(cli.soilgrids, 'descargar', descargar)
    ruta = _archivo(tmp_path, 'error')

    assert 'sigue fallando' in asyncio.run(cli._completar_suelo(None, ruta))
    assert cli._leer(ruta)['sources']['soilgrids']['status'] == 'error'
