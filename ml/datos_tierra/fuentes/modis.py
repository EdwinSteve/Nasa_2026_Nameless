"""MODIS (Terra, colección 061) vía Earth Engine.

- MOD13Q1: NDVI y EVI cada 16 días a 250 m (vigor del lote, fórmula 4.16).
- MOD11A2: temperatura de superficie (LST) cada 8 días a 1 km: calor extremo y
  validación de la corrección de temperatura (ADR 0002).
- MCD12Q1: cobertura del suelo anual (IGBP): saber si el punto es zona de cultivo.
"""
from datetime import date

from . import gee

NDVI = 'MODIS/061/MOD13Q1'
LST = 'MODIS/061/MOD11A2'
COBERTURA = 'MODIS/061/MCD12Q1'
INICIO = date(2000, 2, 18)

CLASES_IGBP = {
    1: 'bosque perennifolio de coníferas', 2: 'bosque perennifolio de latifoliadas',
    3: 'bosque caducifolio de coníferas', 4: 'bosque caducifolio de latifoliadas',
    5: 'bosque mixto', 6: 'matorral cerrado', 7: 'matorral abierto', 8: 'sabana arbolada',
    9: 'sabana', 10: 'pastizal', 11: 'humedal permanente', 12: 'cultivos',
    13: 'urbano', 14: 'mosaico de cultivos y vegetación natural', 15: 'nieve y hielo',
    16: 'suelo desnudo', 17: 'agua',
}
CLASES_CULTIVO = (12, 14)


def _compuestos(coleccion, geometria, escala_m: float) -> list[dict]:
    import ee

    def a_feature(imagen):
        stats = imagen.reduceRegion(reducer=ee.Reducer.mean(), geometry=geometria, scale=escala_m, maxPixels=1e9)
        return ee.Feature(None, stats).set('date', imagen.date().format('YYYY-MM-dd'))

    return [f['properties'] for f in ee.FeatureCollection(coleccion.map(a_feature)).getInfo()['features']]


def _escalar(valor, factor, desplazamiento=0.0, decimales=4):
    return None if valor is None else round(valor * factor + desplazamiento, decimales)


def ultima_cobertura():
    import ee
    return ee.ImageCollection(COBERTURA).select('LC_Type1').sort('system:time_start', False).first()


def descargar(lat, lon, inicio: date, fin: date, poligono=None, buffer_m: float = 5000) -> dict:
    gee.inicializar()
    import ee

    geometria = gee.region(lat, lon, poligono, buffer_m)
    salida = {'source': 'NASA MODIS colección 061 vía Google Earth Engine', 'available_from': INICIO.isoformat(),
              'ndvi': [], 'lst': [], 'land_cover': None}

    cobertura = ultima_cobertura()
    clase = cobertura.reduceRegion(reducer=ee.Reducer.mode(), geometry=geometria, scale=500).get('LC_Type1')
    info = ee.Dictionary({'clase': clase, 'fecha': cobertura.date().format('YYYY')}).getInfo()
    if info.get('clase') is not None:
        codigo = int(info['clase'])
        salida['land_cover'] = {
            'product': COBERTURA, 'year': int(info['fecha']), 'igbp_class': codigo,
            'name': CLASES_IGBP.get(codigo), 'is_cropland': codigo in CLASES_CULTIVO,
        }

    rango = gee.recortar(inicio, fin, INICIO)
    if rango is None:
        return salida
    a, b = rango[0].isoformat(), rango[1].isoformat()

    # Solo píxeles con calidad buena o marginal (SummaryQA 0 o 1).
    ndvi = ee.ImageCollection(NDVI).filterDate(a, b).map(
        lambda img: img.select(['NDVI', 'EVI']).updateMask(img.select('SummaryQA').lte(1))
    )
    salida['ndvi'] = [
        {'date': f['date'], 'ndvi': _escalar(f.get('NDVI'), 0.0001), 'evi': _escalar(f.get('EVI'), 0.0001)}
        for f in _compuestos(ndvi, geometria, 250)
    ]

    lst = ee.ImageCollection(LST).filterDate(a, b).select(['LST_Day_1km', 'LST_Night_1km'])
    salida['lst'] = [
        {
            'date': f['date'],
            'lst_day_c': _escalar(f.get('LST_Day_1km'), 0.02, -273.15, 2),
            'lst_night_c': _escalar(f.get('LST_Night_1km'), 0.02, -273.15, 2),
        }
        for f in _compuestos(lst, geometria, 1000)
    ]
    return salida
