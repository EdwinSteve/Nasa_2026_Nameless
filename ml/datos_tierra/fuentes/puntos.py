"""Selección de puntos de entrenamiento en zonas de cultivo de Colombia (MODIS MCD12Q1)."""
from . import gee, modis

# bbox del Huila usado en el inventario de datos
HUILA_BBOX = [-76.6, 1.5, -74.4, 3.9]


def muestrear(n_colombia: int, n_huila: int, semilla: int = 7) -> list[dict]:
    """Devuelve puntos al azar sobre píxeles de cultivo, con más densidad en el Huila."""
    gee.inicializar()
    import ee

    cobertura = modis.ultima_cobertura()
    cultivos = cobertura.eq(modis.CLASES_CULTIVO[0]).Or(cobertura.eq(modis.CLASES_CULTIVO[1])).selfMask()
    colombia = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filter(ee.Filter.eq('country_na', 'Colombia')).geometry()
    huila = ee.Geometry.Rectangle(HUILA_BBOX)

    def muestra(geometria, cuantos: int):
        return (
            cultivos.sample(region=geometria, scale=500, numPixels=cuantos * 5, seed=semilla, geometries=True)
            .randomColumn('azar', semilla)
            .sort('azar')
            .limit(cuantos)
        )

    puntos = []
    for zona, geometria, cuantos in (('huila', huila, n_huila), ('colombia', colombia.difference(huila, 1000), n_colombia)):
        if cuantos <= 0:
            continue
        for f in muestra(geometria, cuantos).getInfo()['features']:
            lon, lat = f['geometry']['coordinates']
            puntos.append({'id': f'p{len(puntos):04d}', 'lat': round(lat, 5), 'lon': round(lon, 5), 'zona': zona})
    return puntos
