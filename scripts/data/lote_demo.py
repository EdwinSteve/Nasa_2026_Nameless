"""
Puntos 5 y 6 del informe 08: SMAP e IMERG por lote y comparación de riego
(calendario fijo vs balance hídrico) con datos reales del lote demo.

    python scripts/data/lote_demo.py --finca villavieja-seco --siembra 2024-03-16
"""
import argparse
import asyncio
import json
import math
import sys
from datetime import date, timedelta
from pathlib import Path

import httpx

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
sys.path.insert(0, str(BASE / 'agronomic_engine'))
sys.path.insert(0, str(BASE / 'external_apis'))

import imerg  # noqa: E402
import power  # noqa: E402
import smap  # noqa: E402
import soilgrid  # noqa: E402
from engine import calculate_crop_water_requirements, calculate_daily_state  # noqa: E402
from normalizer import (  # noqa: E402
  soilgrids_cfvo_percent,
  soilgrids_fraction,
  soilgrids_soc_to_mo,
)

LAPSE = 0.0065  # °C/m (ADR 0002)
CYCLE_DAYS = 120
CROP_ID = 'maiz'

# Capas de SoilGrids: (etiqueta, tope cm, fondo cm)
SOIL_LAYERS = [
  ('0-5cm', 0, 5), ('5-15cm', 5, 15), ('15-30cm', 15, 30),
  ('30-60cm', 30, 60), ('60-100cm', 60, 100),
]

# Supuestos del informe 08, sección 5, que ahora se reemplazan con datos del lote.
CALENDAR_MM = 40
CALENDAR_EVERY_DAYS = 7
EFFICIENCY = 0.70  # gravedad, como en el informe
SUPUESTOS_INFORME = {
  'et0_media_mm_dia': 4.7, 'kc_medio': 0.85, 'lluvia_efectiva_mm_mes': 66,
  'calendario_mm': 680, 'balance_mm': 306,
}

# Kc del maíz (FAO-56): ini 20 d, desarrollo 35 d, medio 40 d, final 25 d.
def kc_maiz(d: int) -> float:
  if d < 20:
    return 0.30
  if d < 55:
    return 0.30 + 0.90 * (d - 20) / 35
  if d < 95:
    return 1.20
  return 1.20 - 0.85 * (d - 95) / 25


# --- ET0 FAO-56 Penman-Monteith (informe 4.2). Mover a formulas.py cuando se valide. ---
def _e0(t):
  return 0.6108 * math.exp(17.27 * t / (t + 237.3))


def _ra(lat, doy):
  phi = math.radians(lat)
  dr = 1 + 0.033 * math.cos(2 * math.pi / 365 * doy)
  dec = 0.409 * math.sin(2 * math.pi / 365 * doy - 1.39)
  ws = math.acos(-math.tan(phi) * math.tan(dec))
  return (24 * 60 / math.pi) * 0.0820 * dr * (
    ws * math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.sin(ws)
  )


def et0_pm(tmax, tmin, tmax_raw, tmin_raw, rh, u2, rs, lat, z, doy):
  tmean = (tmax + tmin) / 2
  es = (_e0(tmax) + _e0(tmin)) / 2
  # La presión real de vapor se calcula con la T sin corregir: la RH2M de POWER
  # corresponde a la celda de 1400+ m; corregir T y conservar RH inflaría el déficit de vapor.
  ea = rh / 100 * (_e0(tmax_raw) + _e0(tmin_raw)) / 2
  delta = 4098 * _e0(tmean) / (tmean + 237.3) ** 2
  p = 101.3 * ((293 - 0.0065 * z) / 293) ** 5.26
  gamma = 0.000665 * p
  ra = _ra(lat, doy)
  rso = (0.75 + 2e-5 * z) * ra
  rnl = (4.903e-9 * (((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2)
         * (0.34 - 0.14 * math.sqrt(max(ea, 0)))
         * (1.35 * min(rs / rso, 1.0) - 0.35))
  rn = 0.77 * rs - rnl
  num = 0.408 * delta * rn + gamma * 900 / (tmean + 273) * u2 * (es - ea)
  return max(num / (delta + gamma * (1 + 0.34 * u2)), 0.0)


def scs_ratio(p_month: float) -> float:
  """Pe/P según USDA-SCS (informe 4.5)."""
  if p_month <= 0:
    return 1.0
  pe = p_month * (125 - 0.2 * p_month) / 125 if p_month <= 250 else 125 + 0.1 * p_month
  return pe / p_month


def soil_inputs(soil, zr_m):
  """Promedio ponderado por espesor hasta la raíz (informe 4.7) y conversión de unidades."""
  bounds = {label: (top, bottom) for label, top, bottom in SOIL_LAYERS}
  acc, weights = {}, {}
  for layer in soil['properties']['layers']:
    name = layer['name']
    for dep in layer['depths']:
      top, bottom = bounds[dep['label']]
      h = max(0.0, min(bottom, zr_m * 100) - top)
      if h == 0:
        continue
      v = dep['values']['Q0.5']
      if v is None:
        raise ValueError('SoilGrids sin datos para este punto (¿zona urbana o agua?)')
      acc[name] = acc.get(name, 0.0) + v * h
      weights[name] = weights.get(name, 0.0) + h
  raw = {k: acc[k] / weights[k] for k in acc}
  return {
    'sand': soilgrids_fraction(raw['sand']),
    'clay': soilgrids_fraction(raw['clay']),
    'organic_matter': soilgrids_soc_to_mo(raw['soc']),
    'cfvo': soilgrids_cfvo_percent(raw['cfvo']),
  }

async def fetch_soil(client, lat, lon):
  cache = ROOT / f'data/raw/soilgrids_{lat}_{lon}.json'
  if cache.exists():
    return json.loads(cache.read_text(encoding='utf-8'))
  data = await soilgrid.execute(
    client, lat, lon,
    depth=[d for d, _, _ in SOIL_LAYERS],
    statistics=['Q0.5'],
  )
  cache.parent.mkdir(parents=True, exist_ok=True)
  cache.write_text(json.dumps(data), encoding='utf-8')
  return data

async def collect(finca, siembra: date):
  fin = siembra + timedelta(days=CYCLE_DAYS - 1)
  lat, lon = finca['lat'], finca['lon']
  timeout = httpx.Timeout(180, connect=30)
  async with httpx.AsyncClient(timeout=timeout) as client:
    pw, soil, sm, im = await asyncio.gather(
      power.execute(client, lat, lon, f'{siembra:%Y%m%d}', f'{fin:%Y%m%d}'),
      fetch_soil(client, lat, lon),
      smap.execute(lat, lon, siembra.isoformat(), fin.isoformat()),
      imerg.execute(lat, lon, siembra.isoformat(), fin.isoformat()),
    )
  return pw, soil, sm, im


def build_days(finca, siembra, pw, sm, im):
  p = pw['properties']['parameter']
  fill = pw['header'].get('fill_value', -999.0)
  delta = (pw['geometry']['coordinates'][2] - finca['elev_m']) * LAPSE  # ADR 0002
  imerg_by_day = {r['date']: r['precip_mm'] for r in im['serie']}

  def val(name, key):
    v = p[name][key]
    return None if v == fill else v

  days, fallback = [], 0
  for i in range(CYCLE_DAYS):
    d = siembra + timedelta(days=i)
    key = f'{d:%Y%m%d}'
    tmax_raw, tmin_raw = val('T2M_MAX', key), val('T2M_MIN', key)
    rh, u2, rs = val('RH2M', key), val('WS2M', key), val('ALLSKY_SFC_SW_DWN', key)
    if None in (tmax_raw, tmin_raw, rh, u2, rs):
      nombres = ['T2M_MAX', 'T2M_MIN', 'RH2M', 'WS2M', 'ALLSKY_SFC_SW_DWN']
      faltan = [n for n, v in zip(nombres, (tmax_raw, tmin_raw, rh, u2, rs)) if v is None]
      raise SystemExit(
        f'POWER sin datos el {d} ({", ".join(faltan)}). '
        f'Siembra máximo el {d - timedelta(days=CYCLE_DAYS)}.'
      )
    et0 = et0_pm(tmax_raw + delta, tmin_raw + delta, tmax_raw, tmin_raw, rh, u2, rs,
                 finca['lat'], finca['elev_m'], d.timetuple().tm_yday)
    rain = imerg_by_day.get(d.isoformat())
    if rain is None:  # respaldo: POWER
      rain, fallback = (val('PRECTOTCORR', key) or 0.0), fallback + 1
    days.append({'date': d, 'et0': et0, 'etc': kc_maiz(i) * et0, 'rain': max(rain, 0.0)})

  # Lluvia efectiva: razón SCS mensual (prorrateada a 30 d) aplicada a la lluvia diaria.
  by_month = {}
  for x in days:
    by_month.setdefault((x['date'].year, x['date'].month), []).append(x)
  for group in by_month.values():
    equiv = sum(x['rain'] for x in group) / len(group) * 30
    ratio = scs_ratio(equiv)
    for x in group:
      x['pe'] = x['rain'] * ratio

  theta_smap = next((r['sm_rootzone'] for r in sm['serie'] if r['sm_rootzone'] is not None), None)
  if theta_smap is None:
    raise ValueError('SMAP sin datos de zona radicular en la fecha de siembra')
  return days, theta_smap, delta, fallback


def simulate(days, req, policy):
  taw, raw, p = req['taw_mm'], req['raw_mm'], req['p']
  dr, applied, events, stress_days, ks_sum = req['initial_depletion_mm'], 0.0, 0, 0, 0.0
  for i, x in enumerate(days):
    irr_net = 0.0
    if policy == 'balance':
      probe = calculate_daily_state(dr, x['pe'], 0.0, x['etc'], taw, p)
      if probe['should_irrigate']:
        irr_net = min(req['net_irrigation_mm'], probe['depletion_mm'])
        applied += irr_net / EFFICIENCY
        events += 1
    elif (i + 1) % CALENDAR_EVERY_DAYS == 0:
      irr_net = CALENDAR_MM * EFFICIENCY
      applied += CALENDAR_MM
      events += 1
    st = calculate_daily_state(dr, x['pe'], irr_net, x['etc'], taw, p)
    dr = st['depletion_mm']
    ks_sum += st['ks']
    stress_days += st['ks'] < 1.0
  return {
    'riegos': events,
    'lamina_aplicada_mm': round(applied),
    'volumen_m3_ha': round(applied * 10),
    'dias_con_estres': int(stress_days),
    'ks_medio': round(ks_sum / len(days), 3),
  }


async def main():
  ap = argparse.ArgumentParser()
  ap.add_argument('--finca', default='villavieja-seco')
  ap.add_argument('--siembra', default='2024-03-16')  # usar fechas ≤ 2025-09 (IMERG Final)
  a = ap.parse_args()

  fincas = json.loads((ROOT / 'data/fincas_demo.json').read_text(encoding='utf-8'))['fincas']
  finca = next(f for f in fincas if f['id'] == a.finca)
  siembra = date.fromisoformat(a.siembra)

  LATENCIA_DIAS = 5
  ultimo_dia = date.today() - timedelta(days=LATENCIA_DIAS)
  fin = siembra + timedelta(days=CYCLE_DAYS - 1)
  if fin > ultimo_dia:
    raise SystemExit(
      f'El ciclo termina el {fin}, pero los datos llegan hasta ~{ultimo_dia}. '
      f'Siembra máximo el {ultimo_dia - timedelta(days=CYCLE_DAYS - 1)}.'
    )

  pw, soil_raw, sm, im = await collect(finca, siembra)
  days, theta_smap, delta, fallback = build_days(finca, siembra, pw, sm, im)

  from crops import get_crop
  soil = soil_inputs(soil_raw, get_crop(CROP_ID).zr)
  mean_etc = sum(x['etc'] for x in days) / CYCLE_DAYS

  req = calculate_crop_water_requirements(
    crop_id=CROP_ID, **soil, etc=mean_etc,
    theta_smap=theta_smap, irrigation_efficiency=EFFICIENCY,
  )
  calendario = simulate(days, req, 'calendar')
  balance = simulate(days, req, 'balance')
  ahorro_mm = calendario['lamina_aplicada_mm'] - balance['lamina_aplicada_mm']

  rain_total = sum(x['rain'] for x in days)
  pe_total = sum(x['pe'] for x in days)
  res = {
    'finca': finca['id'], 'siembra': a.siembra, 'ciclo_dias': CYCLE_DAYS, 'cultivo': CROP_ID,
    'datos_reales': {
      'et0_media_mm_dia': round(sum(x['et0'] for x in days) / CYCLE_DAYS, 2),
      'kc_medio': round(sum(kc_maiz(i) for i in range(CYCLE_DAYS)) / CYCLE_DAYS, 2),
      'etc_ciclo_mm': round(sum(x['etc'] for x in days)),
      'lluvia_ciclo_mm': round(rain_total),
      'lluvia_efectiva_ciclo_mm': round(pe_total),
      'theta_smap_siembra': round(theta_smap, 3),
      'correccion_temperatura_C': round(delta, 2),
      'dias_lluvia_desde_power_por_falta_de_imerg': fallback,
    },
    'suelo': {k: round(v, 3) for k, v in soil.items()},
    'motor': req,
    'riego_calendario': calendario,
    'riego_balance_hidrico': balance,
    'ahorro': {'mm': ahorro_mm, 'm3_ha': ahorro_mm * 10,
               'pct': round(100 * ahorro_mm / calendario['lamina_aplicada_mm'])},
    'supuestos_informe_seccion_5': SUPUESTOS_INFORME,
    'procedencia': {'smap': sm['coleccion'], 'imerg': im['coleccion'],
                    'power': 'NASA POWER daily/point (AG)', 'suelo': 'SoilGrids 2.0 Q0.5'},
  }
  out = ROOT / f'data/processed/lote_demo_{finca["id"]}.json'
  out.write_text(json.dumps(res, indent=2, ensure_ascii=False, default=str), encoding='utf-8')

  print(f'{finca["nombre"]} · siembra {a.siembra} · maíz {CYCLE_DAYS} d')
  print(f'ET0 {res["datos_reales"]["et0_media_mm_dia"]} mm/d · lluvia efectiva '
        f'{res["datos_reales"]["lluvia_efectiva_ciclo_mm"]} mm · SMAP {theta_smap:.3f}')
  print(f'Calendario: {calendario["lamina_aplicada_mm"]} mm ({calendario["riegos"]} riegos) '
        f'| Balance hídrico: {balance["lamina_aplicada_mm"]} mm ({balance["riegos"]} riegos)')
  print(f'Ahorro: {ahorro_mm} mm = {ahorro_mm * 10} m³/ha ({res["ahorro"]["pct"]} %)')
  print(f'Resultado: {out.relative_to(ROOT)}')


if __name__ == '__main__':
  asyncio.run(main())