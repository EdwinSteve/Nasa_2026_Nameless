"""NASA POWER, serie diaria por punto (comunidad AG).

Una sola petición trae 1981 hasta hoy (verificado: 18 variables × 45 años en ~4 s).
La radiación (ALLSKY, CLRSKY, PAR) empieza en 1984-01-01.
"""
from datetime import date, timedelta

import httpx

from .http import get_con_reintentos

URL = 'https://power.larc.nasa.gov/api/temporal/daily/point'
INICIO = date(1981, 1, 1)
INICIO_RADIACION = date(1984, 1, 1)

# POWER acepta hasta 20 parámetros por petición.
PARAMETROS = [
    'T2M',                # temperatura media a 2 m (°C): trapecios del catálogo
    'T2M_MAX',            # máxima (°C): calor crítico en floración, ET0
    'T2M_MIN',            # mínima (°C): ET0, heladas en zonas altas
    'T2MDEW',             # punto de rocío (°C): presión de vapor real para ET0
    'RH2M',               # humedad relativa (%): trapecio humedad_relativa_pct
    'QV2M',               # humedad específica (g/kg)
    'PRECTOTCORR',        # lluvia corregida (mm/día): trapecio precipitacion_mm
    'WS2M',               # viento a 2 m (m/s): trapecio viento_2m_ms y ET0
    'WS2M_MAX',           # ráfaga diaria (m/s): caída de flores
    'ALLSKY_SFC_SW_DWN',  # radiación de onda corta (MJ/m²/día): ET0
    'CLRSKY_SFC_SW_DWN',  # radiación de cielo despejado (MJ/m²/día): nubosidad
    'ALLSKY_SFC_PAR_TOT', # radiación fotosintéticamente activa (MJ/m²/día)
    'GWETROOT',           # humedad relativa de la zona radicular (0-1), modelo MERRA-2
    'GWETTOP',            # humedad relativa superficial (0-1)
    'GWETPROF',           # humedad relativa del perfil (0-1)
    'PS',                 # presión en superficie (kPa)
    'EVPTRNS',            # evapotranspiración modelada, en MJ/m²/día (derived_evptrns_mm la pasa a mm)
    'TS',                 # temperatura de la superficie (°C)
]
PARAMETROS_RADIACION = {'ALLSKY_SFC_SW_DWN', 'CLRSKY_SFC_SW_DWN', 'ALLSKY_SFC_PAR_TOT'}


# Si la consulta incluye las últimas ~3 semanas (datos casi en tiempo real), POWER devuelve la
# lluvia de TODA la respuesta inflada ~24 veces (verificado el 2026-10-21: 2024 pasa de 1255 mm
# a 30 121 mm si la consulta termina el 2026-10-01; con fin el 2026-09-25 sale bien). Por eso la
# historia se pide hasta DIAS_RECIENTES atrás y el tramo reciente aparte, y la lluvia de ese tramo
# se descarta si es imposible (la lluvia fusionada usa IMERG ahí).
DIAS_RECIENTES = 45
LLUVIA_MAXIMA_DIA_MM = 400.0    # más que el récord diario de Colombia: es un dato corrupto
LLUVIA_MAXIMA_MEDIA_MM = 30.0   # media diaria imposible para un tramo de semanas


async def _consultar(cliente: httpx.AsyncClient, lat: float, lon: float, inicio: date, fin: date) -> dict:
    params = {
        'parameters': ','.join(PARAMETROS),
        'community': 'AG',
        'latitude': lat,
        'longitude': lon,
        'start': f'{inicio:%Y%m%d}',
        'end': f'{fin:%Y%m%d}',
        'format': 'JSON',
    }
    respuesta = await get_con_reintentos(cliente, URL, params)
    return respuesta.json()


def lluvia_corrupta(crudo: dict) -> bool:
    relleno = crudo.get('header', {}).get('fill_value', -999.0)
    valores = [v for v in crudo['properties']['parameter'].get('PRECTOTCORR', {}).values() if v != relleno]
    return bool(valores) and (max(valores) > LLUVIA_MAXIMA_DIA_MM or sum(valores) / len(valores) > LLUVIA_MAXIMA_MEDIA_MM)


async def descargar(cliente: httpx.AsyncClient, lat: float, lon: float, inicio: date, fin: date,
                    hoy: date | None = None) -> dict:
    """Serie diaria de POWER. Mismo formato que la API, con 'avisos' si se descartó lluvia."""
    corte = (hoy or date.today()) - timedelta(days=DIAS_RECIENTES)
    if fin <= corte:
        return await _consultar(cliente, lat, lon, inicio, fin)

    partes = []
    if inicio <= corte:
        partes.append(await _consultar(cliente, lat, lon, inicio, corte))
    reciente = await _consultar(cliente, lat, lon, max(inicio, corte + timedelta(days=1)), fin)
    avisos = []
    if lluvia_corrupta(reciente):
        relleno = reciente.get('header', {}).get('fill_value', -999.0)
        reciente['properties']['parameter']['PRECTOTCORR'] = {
            k: relleno for k in reciente['properties']['parameter']['PRECTOTCORR']
        }
        avisos.append(
            f'POWER devolvió lluvia imposible para los últimos {DIAS_RECIENTES} días: se descartó '
            '(la lluvia de ese tramo sale de IMERG).'
        )
    partes.append(reciente)

    unida = partes[0]
    for parte in partes[1:]:
        for nombre, valores in parte['properties']['parameter'].items():
            unida['properties']['parameter'].setdefault(nombre, {}).update(valores)
    if avisos:
        unida['avisos'] = avisos
    return unida


def series(crudo: dict) -> tuple[dict[str, dict[str, float | None]], dict]:
    """Convierte la respuesta en {parametro: {fecha ISO: valor}} con -999 -> None."""
    relleno = crudo.get('header', {}).get('fill_value', -999.0)
    salida = {
        nombre: {f'{k[:4]}-{k[4:6]}-{k[6:]}': (None if v == relleno else v) for k, v in valores.items()}
        for nombre, valores in crudo['properties']['parameter'].items()
    }
    meta = {
        'endpoint': URL,
        'community': 'AG',
        'cell_elevation_m': crudo['geometry']['coordinates'][2],
        'units': {k: v.get('units') for k, v in crudo.get('parameters', {}).items()},
    }
    if crudo.get('avisos'):
        meta['warnings'] = crudo['avisos']
    return salida, meta
