"""Selección de puntos de entrenamiento en zonas de cultivo de Colombia.

Cultivo = MODIS MCD12Q1 (IGBP 12 y 14, 500 m) o ESA WorldCover (clase 40, 10 m). MODIS
solo ve el cultivo extensivo; WorldCover agrega las parcelas pequeñas de ladera.
"""
import math
import random

from . import gee, modis

# bbox del Huila usado en el inventario de datos
HUILA_BBOX = [-76.6, 1.5, -74.4, 3.9]
WORLDCOVER = 'ESA/WorldCover/v200'
WORLDCOVER_CULTIVO = 40

# Distancia mínima entre puntos. Sin ella los puntos se amontonan donde hay más cultivo
# (mediana de 2 km al vecino) y muchos caen en la misma celda de SMAP (9 km).
# Con 6 y 15 km caben ~130 puntos en el Huila y ~250 en el resto: el área agrícola no da para 600.
DISTANCIA_MIN_KM = {'huila': 6.0, 'colombia': 15.0}
CANDIDATOS_POR_PUNTO = 10  # getInfo() admite hasta 5000 elementos por consulta


def distancia_km(a: dict, b: dict) -> float:
    """Distancia aproximada (equirectangular): sobra precisión para separar puntos."""
    lat_media = math.radians((a['lat'] + b['lat']) / 2)
    return 111.2 * math.hypot(a['lat'] - b['lat'], (a['lon'] - b['lon']) * math.cos(lat_media))


def espaciar(candidatos: list[dict], cuantos: int, minimo_km: float, ocupados: list[dict], semilla: int) -> list[dict]:
    """Recorre los candidatos en orden aleatorio fijo y acepta los que quedan lejos de los ya elegidos."""
    orden = sorted(candidatos, key=lambda c: (c['lat'], c['lon']))
    random.Random(semilla).shuffle(orden)
    elegidos = []
    for c in orden:
        if len(elegidos) == cuantos:
            break
        if all(distancia_km(c, o) >= minimo_km for o in ocupados + elegidos):
            elegidos.append(c)
    return elegidos


def muestrear(n_colombia: int, n_huila: int, semilla: int = 7) -> list[dict]:
    """Devuelve puntos al azar sobre píxeles de cultivo, separados entre sí, con más densidad en el Huila."""
    gee.inicializar()
    import ee

    cobertura = modis.ultima_cobertura()
    worldcover = ee.ImageCollection(WORLDCOVER).first().eq(WORLDCOVER_CULTIVO)
    cultivos = (
        cobertura.eq(modis.CLASES_CULTIVO[0]).Or(cobertura.eq(modis.CLASES_CULTIVO[1])).Or(worldcover)
        .selfMask().rename('cultivo').toInt()
    )
    colombia = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filter(ee.Filter.eq('country_na', 'Colombia')).geometry()
    huila = ee.Geometry.Rectangle(HUILA_BBOX)

    def candidatos(geometria, cuantos: int) -> list[dict]:
        # stratifiedSample sortea solo entre los píxeles de cultivo (los demás están enmascarados).
        # sample(numPixels=...) sorteaba en toda la región y descartaba casi todo: de 600 quedaban 46.
        muestra = cultivos.stratifiedSample(
            numPoints=min(cuantos * CANDIDATOS_POR_PUNTO, 5000), classBand='cultivo', region=geometria,
            scale=500, seed=semilla, geometries=True, tileScale=4,
        )
        salida = []
        for f in muestra.getInfo()['features']:
            lon, lat = f['geometry']['coordinates']
            salida.append({'lat': round(lat, 5), 'lon': round(lon, 5)})
        return salida

    puntos: list[dict] = []
    for zona, geometria, cuantos in (('huila', huila, n_huila), ('colombia', colombia.difference(huila, 1000), n_colombia)):
        if cuantos <= 0:
            continue
        elegidos = espaciar(candidatos(geometria, cuantos), cuantos, DISTANCIA_MIN_KM[zona], puntos, semilla)
        if len(elegidos) < cuantos:
            print(f'Aviso: en {zona} solo caben {len(elegidos)} de {cuantos} puntos a {DISTANCIA_MIN_KM[zona]} km entre sí.')
        for c in elegidos:
            puntos.append({'id': f'p{len(puntos):04d}', **c, 'zona': zona})
    return puntos
