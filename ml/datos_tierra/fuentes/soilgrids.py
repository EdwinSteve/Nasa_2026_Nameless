"""ISRIC SoilGrids 2.0 (250 m). Estático: no depende del rango de fechas.

Límite público: ~5 consultas por minuto. En zonas urbanas devuelve null.
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


async def descargar(cliente: httpx.AsyncClient, lat: float, lon: float) -> dict:
    params = {
        'lon': lon,
        'lat': lat,
        'property': PROPIEDADES,
        'depth': PROFUNDIDADES,
        'value': ESTADISTICAS,
    }
    respuesta = await get_con_reintentos(cliente, URL, params, intentos=4, espera_s=15)
    return respuesta.json()
