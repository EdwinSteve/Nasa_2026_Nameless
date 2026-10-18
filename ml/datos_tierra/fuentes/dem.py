"""Elevación real del punto con SRTM 30 m (NASA) vía OpenTopoData.

Es la elevación que necesita la corrección de temperatura (ADR 0002) y la
métrica altitud_msnm del catálogo. API pública: 100 puntos por consulta,
1 consulta por segundo, 1000 por día.
"""
import asyncio

import httpx

from .http import get_con_reintentos

URL = 'https://api.opentopodata.org/v1/srtm30m'
FUENTE = 'NASA SRTM 30 m (OpenTopoData)'
PUNTOS_POR_CONSULTA = 100


async def elevaciones(cliente: httpx.AsyncClient, puntos: list[tuple[float, float]]) -> list[float | None]:
    """puntos: lista de (lat, lon). Devuelve la elevación en m en el mismo orden."""
    resultado: list[float | None] = []
    for i in range(0, len(puntos), PUNTOS_POR_CONSULTA):
        if i:
            await asyncio.sleep(1.1)
        lote = puntos[i:i + PUNTOS_POR_CONSULTA]
        locations = '|'.join(f'{lat},{lon}' for lat, lon in lote)
        respuesta = await get_con_reintentos(cliente, URL, {'locations': locations})
        resultado += [r.get('elevation') for r in respuesta.json()['results']]
    return resultado
