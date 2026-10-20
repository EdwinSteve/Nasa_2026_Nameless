"""ISRIC SoilGrids 2.0 (250 m). Estático: no depende del rango de fechas.

Límite público: ~5 consultas por minuto. En zonas urbanas devuelve null.

Pedir todas las propiedades en una sola consulta hace que el servidor responda
504 a los 180 s (verificado el 2026-10-20). En bloques de 3 propiedades cada
consulta tarda de 20 a 35 s, así que la consulta se parte y las capas se unen.
"""
import httpx

from .http import get_con_reintentos

URL = 'https://rest.isric.org/soilgrids/v2.0/properties/query'

PROPIEDADES = [
    'sand', 'silt', 'clay',   # textura: Saxton & Rawls, TAW
    'soc',                    # carbono orgánico -> materia orgánica
    'cfvo',                   # fragmentos gruesos: corrección de TAW
    'bdod',                   # densidad aparente
    'phh2o',                  # pH: trapecio ph del catálogo
    'cec',                    # capacidad de intercambio catiónico
    'nitrogen',               # N total: trapecio N_O_CUL del catálogo
    'ocd',                    # densidad de carbono orgánico
    'wv0033', 'wv1500',       # agua a capacidad de campo y marchitez: contraste de Saxton & Rawls
]
# Hasta 200 cm: las raíces del catálogo llegan a 1,2 m (caña).
PROFUNDIDADES = ['0-5cm', '5-15cm', '15-30cm', '30-60cm', '60-100cm', '100-200cm']
ESTADISTICAS = ['mean', 'Q0.05', 'Q0.5', 'Q0.95']
PROPIEDADES_POR_CONSULTA = 3


async def descargar(
    cliente: httpx.AsyncClient,
    lat: float,
    lon: float,
    propiedades: list[str] = PROPIEDADES,
    profundidades: list[str] = PROFUNDIDADES,
    estadisticas: list[str] = ESTADISTICAS,
    por_consulta: int = PROPIEDADES_POR_CONSULTA,
) -> dict:
    """Devuelve la misma forma que una sola respuesta de SoilGrids, con todas las capas pedidas.

    Las consultas van una tras otra (no en paralelo) para respetar el límite por minuto.
    """
    unida: dict | None = None
    for i in range(0, len(propiedades), por_consulta):
        params = {
            'lon': lon,
            'lat': lat,
            'property': list(propiedades[i:i + por_consulta]),
            'depth': list(profundidades),
            'value': list(estadisticas),
        }
        respuesta = (await get_con_reintentos(cliente, URL, params, intentos=4, espera_s=15)).json()
        if unida is None:
            unida = respuesta
        else:
            unida['properties']['layers'].extend(respuesta['properties']['layers'])
    return unida or {'properties': {'layers': []}}
