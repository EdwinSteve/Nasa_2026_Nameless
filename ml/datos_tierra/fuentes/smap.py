"""NASA SMAP L4 (SPL4SMGP), humedad del suelo a 9 km, vía Earth Engine.

Disponible desde el 2015-03-31. Ocho pasadas de 3 h se promedian por día.
"""
from datetime import date

from . import gee

COLECCIONES = ['NASA/SMAP/SPL4SMGP/008', 'NASA/SMAP/SPL4SMGP/007']
INICIO = date(2015, 3, 31)
ESCALA_M = 9000
SEGUNDOS_DIA = 86400

# banda de GEE -> nombre de columna. Solo se piden las que existan en la colección.
BANDAS = {
    'sm_surface': 'sm_surface',          # m³/m³, 0-5 cm
    'sm_rootzone': 'sm_rootzone',        # m³/m³, 0-100 cm: agotamiento inicial (4.13)
    'sm_profile': 'sm_profile',          # m³/m³, perfil completo
    'land_evapotranspiration_flux': 'land_et_mm',  # kg/m²/s -> mm/día: ET real modelada
}


def _convertir(banda: str, valor: float | None) -> float | None:
    if valor is None:
        return None
    if banda == 'land_evapotranspiration_flux':
        return valor * SEGUNDOS_DIA
    return valor


def descargar(lat, lon, inicio: date, fin: date, poligono=None, buffer_m: float = 5000) -> dict:
    gee.inicializar()
    import ee

    meta = {'source': 'NASA SMAP L4 (SPL4SMGP) vía Google Earth Engine', 'resolution_m': ESCALA_M,
            'units': 'm3/m3 (land_et_mm en mm/día)', 'available_from': INICIO.isoformat()}
    rango = gee.recortar(inicio, fin, INICIO)
    if rango is None:
        return {**meta, 'collection': None, 'bands': [], 'series': []}

    ultimo_error = None
    for coleccion_id in COLECCIONES:
        try:
            coleccion = ee.ImageCollection(coleccion_id)
            disponibles = coleccion.first().bandNames().getInfo()
            bandas = [b for b in BANDAS if b in disponibles]
            coleccion = coleccion.select(bandas)

            def imagen_del_dia(dia):
                del_dia = coleccion.filterDate(dia, dia.advance(1, 'day'))
                return del_dia.mean(), del_dia.size()

            filas = gee.serie_diaria(imagen_del_dia, gee.region(lat, lon, poligono, buffer_m), *rango, ESCALA_M)
            return {
                **meta,
                'collection': coleccion_id,
                'bands': [BANDAS[b] for b in bandas],
                'bands_missing': [BANDAS[b] for b in BANDAS if b not in bandas],
                'series': [
                    {'date': f['date'], **{BANDAS[b]: _convertir(b, f.get(b)) for b in bandas}}
                    for f in filas
                ],
            }
        except ee.EEException as exc:
            ultimo_error = exc

    raise RuntimeError(f'No se pudo leer SMAP L4 en Earth Engine: {ultimo_error}')
