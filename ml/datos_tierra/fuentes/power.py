"""NASA POWER, serie diaria por punto (comunidad AG).

Una sola petición trae 1981 hasta hoy (verificado: 18 variables × 45 años en ~4 s).
La radiación (ALLSKY, CLRSKY, PAR) empieza en 1984-01-01.
"""
from datetime import date

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


async def descargar(cliente: httpx.AsyncClient, lat: float, lon: float, inicio: date, fin: date) -> dict:
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
    return salida, meta
