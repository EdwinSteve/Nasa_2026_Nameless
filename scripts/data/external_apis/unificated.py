"""
Unifica POWER + SoilGrids + SMAP + IMERG en un solo JSON para un punto/polígono
y un rango de fechas. No calcula nada agronómico ni predictivo: solo normaliza la
forma (fechas ISO, -999 -> null, una fila por día) para poder persistirlo.
"""
import asyncio
from datetime import date, datetime, timedelta, timezone

import httpx

import imerg
import power
import smap
import soilgrid

SCHEMA_VERSION = '1.0'
SOIL_DEPTHS = ['0-5cm', '5-15cm', '15-30cm', '30-60cm', '60-100cm']
SOIL_STATS = ['Q0.05', 'Q0.5', 'Q0.95']


def _iso_days(start: date, end: date) -> list[str]:
  return [(start + timedelta(days=i)).isoformat() for i in range((end - start).days + 1)]


def _power(raw: dict) -> tuple[dict, dict]:
  fill = raw.get('header', {}).get('fill_value', -999.0)
  series = {
    name: {f'{k[:4]}-{k[4:6]}-{k[6:]}': (None if v == fill else v) for k, v in vals.items()}
    for name, vals in raw['properties']['parameter'].items()
  }
  meta = {
    'endpoint': power.NASA_POWER_URL,
    'community': 'AG',
    'cell_elevation_m': raw['geometry']['coordinates'][2],  # sirve luego para la corrección ADR 0002
    'units': {k: v.get('units') for k, v in raw.get('parameters', {}).items()},
  }
  return series, meta


def _soil(raw: dict) -> tuple[dict, dict]:
  """Valores tal cual los entrega SoilGrids (unidades 'mapped'); la conversión
  se hace después en normalizer.py. Se guarda d_factor para poder reconstruirla."""
  layers, units = {}, {}
  for layer in raw['properties']['layers']:
    um = layer['unit_measure']
    units[layer['name']] = {
      'mapped_units': um.get('mapped_units'),
      'target_units': um.get('target_units'),
      'd_factor': um.get('d_factor'),
    }
    for dep in layer['depths']:
      layers.setdefault(dep['label'], {})[layer['name']] = dep['values']  # {Q0.05, Q0.5, Q0.95}
  return layers, {'endpoint': soilgrid.SOIL_GRID_URL, 'units': units}


def _rows(serie: list[dict], key: str) -> dict:
  return {r['date']: r.get(key) for r in serie}


async def execute(
  client: httpx.AsyncClient,
  lat: float,
  lon: float,
  start_date: str,
  end_date: str,
  polygon: list[list[float]] | None = None,
  buffer_m: float = 5000,
) -> dict:
  start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
  if end < start:
    raise ValueError('end_date no puede ser anterior a start_date.')

  names = ['power', 'soilgrids', 'smap', 'imerg']
  results = await asyncio.gather(
    power.execute(client, lat, lon, f'{start:%Y%m%d}', f'{end:%Y%m%d}'),
    soilgrid.execute(client, lat, lon, depth=SOIL_DEPTHS, statistics=SOIL_STATS),
    smap.execute(lat, lon, start_date, end_date, polygon, buffer_m),
    imerg.execute(lat, lon, start_date, end_date, polygon, buffer_m),
    return_exceptions=True,  # una fuente caída no tumba las demás
  )

  sources, data = {}, {}
  for name, res in zip(names, results):
    if isinstance(res, Exception):
      sources[name] = {'status': 'error', 'error': f'{type(res).__name__}: {res}'}
    else:
      data[name] = res
      sources[name] = {'status': 'ok'}

  days = _iso_days(start, end)
  rows = {d: {'date': d} for d in days}

  # POWER
  p_series = {}
  if 'power' in data:
    p_series, meta = _power(data['power'])
    sources['power'].update(meta)
  for name in power.POWER_PARAMETERS:
    for d in days:
      rows[d][f'power_{name.lower()}'] = p_series.get(name, {}).get(d)

  # SMAP
  sm = data.get('smap')
  if sm:
    sources['smap'].update({k: sm[k] for k in ('fuente', 'coleccion', 'unidad', 'resolucion_m')})
  for band in smap.SMAP_BANDS:
    vals = _rows(sm['serie'], band) if sm else {}
    for d in days:
      rows[d][f'smap_{band}'] = vals.get(d)

  # IMERG
  im = data.get('imerg')
  if im:
    sources['imerg'].update({k: im[k] for k in ('fuente', 'coleccion', 'unidad', 'resolucion_m')})
  vals = _rows(im['serie'], 'precip_mm') if im else {}
  for d in days:
    rows[d]['imerg_precip_mm'] = vals.get(d)

  # SoilGrids (estático: no depende del rango de fechas)
  soil = None
  if 'soilgrids' in data:
    soil, meta = _soil(data['soilgrids'])
    sources['soilgrids'].update(meta)

  daily = list(rows.values())
  columns = [c for c in daily[0] if c != 'date']
  return {
    'schema_version': SCHEMA_VERSION,
    'fetched_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    'location': {'lat': lat, 'lon': lon, 'polygon': polygon, 'buffer_m': None if polygon else buffer_m},
    'period': {'start': start_date, 'end': end_date, 'days': len(days)},
    'sources': sources,
    'soil': soil,
    'daily': daily,
    'quality': {'missing_days': {c: sum(r[c] is None for r in daily) for c in columns}},
  }

if __name__ == '__main__':
  import argparse
  import json
  from pathlib import Path

  ROOT = Path(__file__).resolve().parents[3]

  async def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lat', type=float, default=3.22)
    ap.add_argument('--lon', type=float, default=-75.22)
    ap.add_argument('--inicio', default='2026-08-01')
    ap.add_argument('--fin', default='2026-08-07')
    ap.add_argument('--out', default=None)
    a = ap.parse_args()

    async with httpx.AsyncClient(timeout=httpx.Timeout(180, connect=30)) as client:
      res = await execute(client, a.lat, a.lon, a.inicio, a.fin)

    out = Path(a.out) if a.out else ROOT / f'data/processed/unified_{a.lat}_{a.lon}_{a.inicio}_{a.fin}.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding='utf-8')

    print({k: v['status'] for k, v in res['sources'].items()})
    print('días:', res['period']['days'], '| faltantes:', res['quality']['missing_days'])
    print('Guardado en', out)

  asyncio.run(_main())