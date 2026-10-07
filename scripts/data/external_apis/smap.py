import asyncio
import os
from datetime import date

import ee

# Verificar versión vigente en el catálogo de GEE (el informe 08 también lo pide).
SMAP_COLLECTIONS = [
  'NASA/SMAP/SPL4SMGP/008',
  'NASA/SMAP/SPL4SMGP/007',
]
SMAP_BANDS = ['sm_surface', 'sm_rootzone']  # m³/m³
SMAP_SCALE_M = 9000


def _init_ee():
  ee.Initialize(project=os.environ.get('GEE_PROJECT'))


def _region(lat, lon, polygon, buffer_m):
  """polygon: lista de [lon, lat]. Si no hay, se usa un buffer alrededor del punto."""
  if polygon:
    return ee.Geometry.Polygon([polygon])
  return ee.Geometry.Point([lon, lat]).buffer(buffer_m)


def _fetch(collection_id, region, start_date, end_date):
  col = ee.ImageCollection(collection_id).select(SMAP_BANDS)
  t0 = ee.Date(start_date)
  n_days = (date.fromisoformat(end_date) - date.fromisoformat(start_date)).days + 1

  def per_day(i):
    day = t0.advance(ee.Number(i), 'day')
    img = col.filterDate(day, day.advance(1, 'day')).mean()  # 8 pasadas de 3 h -> media diaria
    stats = img.reduceRegion(
      reducer=ee.Reducer.mean(),
      geometry=region,
      scale=SMAP_SCALE_M,
    )
    return ee.Feature(None, stats).set('date', day.format('YYYY-MM-dd'))

  fc = ee.FeatureCollection(ee.List.sequence(0, n_days - 1).map(per_day))
  return [f['properties'] for f in fc.getInfo()['features']]  # límite de GEE: 5000 elementos


def _execute_sync(lat, lon, start_date, end_date, polygon, buffer_m):
  _init_ee()
  region = _region(lat, lon, polygon, buffer_m)
  last_error = None

  for collection_id in SMAP_COLLECTIONS:
    try:
      rows = _fetch(collection_id, region, start_date, end_date)
      return {
        'fuente': 'NASA SMAP L4 (SPL4SMGP) vía Google Earth Engine',
        'coleccion': collection_id,
        'unidad': 'm3/m3',
        'resolucion_m': SMAP_SCALE_M,
        'serie': [
          {
            'date': r['date'],
            'sm_surface': r.get('sm_surface'),
            'sm_rootzone': r.get('sm_rootzone'),
          }
          for r in rows
        ],
      }
    except ee.EEException as exc:
      last_error = exc

  raise RuntimeError(f'No se pudo leer SMAP L4 en Earth Engine: {last_error}')


async def execute(
  lat: float,
  lon: float,
  start_date: str,
  end_date: str,
  polygon: list[list[float]] | None = None,
  buffer_m: float = 5000,
):
  """Earth Engine usa su propio cliente, por eso no recibe httpx.AsyncClient."""
  return await asyncio.to_thread(
    _execute_sync, lat, lon, start_date, end_date, polygon, buffer_m
  )