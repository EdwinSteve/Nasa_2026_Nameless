import asyncio
import os
from datetime import date

import ee

# (colección, banda). La banda de V07 es 'precipitation' (mm/h, pasos de 30 min).
IMERG_SOURCES = [
  ('NASA/GPM_L3/IMERG_V07', 'precipitation'),
  ('NASA/GPM_L3/IMERG_V06', 'precipitationCal'),
]
IMERG_SCALE_M = 11000
HOURS_PER_STEP = 0.5  # mm/h x 0.5 h = mm por imagen


def _init_ee():
  ee.Initialize(project=os.environ.get('GEE_PROJECT'))


def _region(lat, lon, polygon, buffer_m):
  if polygon:
    return ee.Geometry.Polygon([polygon])
  return ee.Geometry.Point([lon, lat]).buffer(buffer_m)


def _fetch(collection_id, band, region, start_date, end_date):
  col = ee.ImageCollection(collection_id).select(band)
  t0 = ee.Date(start_date)
  n_days = (date.fromisoformat(end_date) - date.fromisoformat(start_date)).days + 1

  def per_day(i):
    day = t0.advance(ee.Number(i), 'day')
    day_col = col.filterDate(day, day.advance(1, 'day'))
    total = day_col.sum().multiply(HOURS_PER_STEP)
    stats = total.reduceRegion(
      reducer=ee.Reducer.mean(),
      geometry=region,
      scale=IMERG_SCALE_M,
    )
    return (
      ee.Feature(None, stats)
      .set('date', day.format('YYYY-MM-dd'))
      .set('n_img', day_col.size())
    )

  fc = ee.FeatureCollection(ee.List.sequence(0, n_days - 1).map(per_day))
  return [f['properties'] for f in fc.getInfo()['features']]


def _execute_sync(lat, lon, start_date, end_date, polygon, buffer_m):
  _init_ee()
  region = _region(lat, lon, polygon, buffer_m)
  last_error = None

  for collection_id, band in IMERG_SOURCES:
    try:
      rows = _fetch(collection_id, band, region, start_date, end_date)
      return {
        'fuente': 'NASA GPM IMERG vía Google Earth Engine',
        'coleccion': collection_id,
        'unidad': 'mm/dia',
        'resolucion_m': IMERG_SCALE_M,
        'serie': [
          {
            'date': r['date'],
            # Un día sin imágenes no es "0 mm": es un dato faltante.
            'precip_mm': r.get(band) if r.get('n_img', 0) > 0 else None,
          }
          for r in rows
        ],
      }
    except ee.EEException as exc:
      last_error = exc

  raise RuntimeError(f'No se pudo leer IMERG en Earth Engine: {last_error}')


async def execute(
  lat: float,
  lon: float,
  start_date: str,
  end_date: str,
  polygon: list[list[float]] | None = None,
  buffer_m: float = 5000,
):
  return await asyncio.to_thread(
    _execute_sync, lat, lon, start_date, end_date, polygon, buffer_m
  )