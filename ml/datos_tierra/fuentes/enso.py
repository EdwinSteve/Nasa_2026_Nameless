"""Índice Oceánico de El Niño (ONI) de NOAA CPC.

Es la principal fuente de predictibilidad estacional del clima en Colombia:
el modelo lo usa para anticipar el ciclo. No depende del lote.
"""
from datetime import date

import httpx

from .http import get_con_reintentos

URL = 'https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt'
FUENTE = 'NOAA CPC, ONI (anomalía SST Niño 3.4, media móvil de 3 meses)'

# El año de la tabla es el del mes central: "DJF 1950" = dic 1949 a feb 1950.
MES_CENTRAL = {
    'DJF': 1, 'JFM': 2, 'FMA': 3, 'MAM': 4, 'AMJ': 5, 'MJJ': 6,
    'JJA': 7, 'JAS': 8, 'ASO': 9, 'SON': 10, 'OND': 11, 'NDJ': 12,
}


async def descargar(cliente: httpx.AsyncClient) -> str:
    respuesta = await get_con_reintentos(cliente, URL)
    return respuesta.text


def parsear(texto: str) -> list[dict]:
    filas = []
    for linea in texto.splitlines():
        partes = linea.split()
        if len(partes) != 4 or partes[0] not in MES_CENTRAL:
            continue
        temporada, anio, _total, anomalia = partes
        filas.append({
            'season': temporada,
            'year': int(anio),
            'month': MES_CENTRAL[temporada],
            'oni': float(anomalia),
            'phase': fase(float(anomalia)),
        })
    return filas


def fase(oni: float) -> str:
    """Umbral operativo de NOAA: ±0,5 °C."""
    if oni >= 0.5:
        return 'el_nino'
    if oni <= -0.5:
        return 'la_nina'
    return 'neutral'


def filtrar(filas: list[dict], desde: date, hasta: date) -> list[dict]:
    return [f for f in filas if desde <= date(f['year'], f['month'], 1) <= hasta]
