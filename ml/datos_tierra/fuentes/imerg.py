"""NASA GPM IMERG V07, lluvia a ~11 km, vía Earth Engine.

Disponible desde el 2000-06-01. La banda viene en mm/h en pasos de 30 min.
"""
from datetime import date

from . import gee

COLECCION = 'NASA/GPM_L3/IMERG_V07'
BANDA = 'precipitation'
INICIO = date(2000, 6, 1)
ESCALA_M = 11000
HORAS_POR_PASO = 0.5  # mm/h × 0,5 h = mm por imagen


def descargar(lat, lon, inicio: date, fin: date, poligono=None, buffer_m: float = 5000) -> dict:
    gee.inicializar()
    import ee

    meta = {'source': 'NASA GPM IMERG V07 vía Google Earth Engine', 'collection': COLECCION,
            'units': 'mm/dia', 'resolution_m': ESCALA_M, 'available_from': INICIO.isoformat()}
    rango = gee.recortar(inicio, fin, INICIO)
    if rango is None:
        return {**meta, 'series': []}

    coleccion = ee.ImageCollection(COLECCION).select(BANDA)

    def imagen_del_dia(dia):
        del_dia = coleccion.filterDate(dia, dia.advance(1, 'day'))
        return del_dia.sum(), del_dia.size()

    try:
        filas = gee.serie_diaria(imagen_del_dia, gee.region(lat, lon, poligono, buffer_m), *rango, ESCALA_M)
    except ee.EEException as exc:
        raise RuntimeError(f'No se pudo leer IMERG en Earth Engine: {exc}') from exc

    return {
        **meta,
        'series': [
            {
                'date': f['date'],
                # Un día sin imágenes no es "0 mm": es un dato faltante.
                'precip_mm': f[BANDA] * HORAS_POR_PASO if f.get('n_img') and f.get(BANDA) is not None else None,
            }
            for f in filas
        ],
    }
