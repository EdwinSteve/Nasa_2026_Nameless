from collections import OrderedDict

import httpx

URL = "https://api.opentopodata.org/v1/srtm30m"
CACHE_MAXIMO = 2_000
# 4 decimales ≈ 11 m: la misma celda SRTM de 30 m, así que el resultado no cambia.
DECIMALES_CACHE = 4


class ElevacionSRTM:
    """Modelo de elevación NASA SRTM de 30 m vía OpenTopoData (el mismo del diagnóstico).

    La API pública permite 1 consulta por segundo y 1000 por día: se guardan en memoria
    las últimas respuestas para no repetir la consulta de un mismo lugar.
    """

    fuente = "NASA SRTM"

    def __init__(self, url: str = URL, timeout_s: float = 10.0) -> None:
        self._url = url
        self._timeout = timeout_s
        self._cache: OrderedDict[tuple[float, float], float | None] = OrderedDict()

    async def altitud(self, lat: float, lon: float) -> float | None:
        clave = (round(lat, DECIMALES_CACHE), round(lon, DECIMALES_CACHE))
        if clave in self._cache:
            self._cache.move_to_end(clave)
            return self._cache[clave]

        async with httpx.AsyncClient(timeout=self._timeout) as cliente:
            respuesta = await cliente.get(self._url, params={"locations": f"{clave[0]},{clave[1]}"})
            respuesta.raise_for_status()
        altitud = respuesta.json()["results"][0].get("elevation")

        self._cache[clave] = altitud
        if len(self._cache) > CACHE_MAXIMO:
            self._cache.popitem(last=False)
        return altitud
