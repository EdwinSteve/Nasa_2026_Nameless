import asyncio

import httpx

REINTENTABLES = {429, 500, 502, 503, 504}


async def get_con_reintentos(
    cliente: httpx.AsyncClient,
    url: str,
    params: dict | None = None,
    intentos: int = 3,
    espera_s: float = 10,
) -> httpx.Response:
    """GET con reintentos para timeouts, caídas de red y los códigos de REINTENTABLES."""
    for intento in range(1, intentos + 1):
        try:
            respuesta = await cliente.get(url, params=params)
            respuesta.raise_for_status()
            return respuesta
        except (httpx.TransportError, httpx.HTTPStatusError) as exc:
            reintentable = (
                not isinstance(exc, httpx.HTTPStatusError)
                or exc.response.status_code in REINTENTABLES
            )
            if not reintentable or intento == intentos:
                raise
            await asyncio.sleep(espera_s * intento)
    raise AssertionError('inalcanzable')
