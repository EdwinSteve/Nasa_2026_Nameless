"""SoilGrids 2.0 publicado en Google Earth Engine (projects/soilgrids-isric): respaldo de la API REST.

Mismos mapas y mismas unidades 'mapped' que la API de ISRIC, así que suelo.procesar() los
convierte igual. Diferencias: solo trae la media (Q0.5 se toma igual a la media y no hay
Q0.05/Q0.95, así que no hay incertidumbre) y no tiene wv0033 ni wv1500.
"""
from . import gee
from .soilgrids import PROFUNDIDADES

ACTIVO = 'projects/soilgrids-isric/{}_mean'
# Propiedad -> (divisor, unidades convencionales). Iguales a los d_factor de la API REST salvo el
# nitrógeno, que en Earth Engine viene en mg/kg: en Campoalegre (2.69, -75.33, 0-5 cm) la API da
# 2,55 g/kg y Earth Engine 2515. Arcilla, arena, pH y SOC coinciden con la API en ese punto.
PROPIEDADES = {
    'bdod': (100, 'kg/dm³'), 'cec': (10, 'cmol(c)/kg'), 'cfvo': (10, 'cm³/100cm³'), 'clay': (10, '%'),
    'nitrogen': (1000, 'g/kg'), 'ocd': (10, 'kg/m³'), 'phh2o': (10, 'pH'), 'sand': (10, '%'),
    'silt': (10, '%'), 'soc': (10, 'g/kg'),
}
FUENTE = 'ISRIC SoilGrids 2.0 (media) vía Google Earth Engine'
ESCALA_M = 250


def _rango(etiqueta: str) -> tuple[int, int]:
    arriba, abajo = etiqueta.removesuffix('cm').split('-')
    return int(arriba), int(abajo)


def descargar(lat: float, lon: float) -> dict:
    """Devuelve la misma estructura que la API REST de SoilGrids (properties.layers)."""
    gee.inicializar()
    import ee

    imagen = ee.Image.cat([ee.Image(ACTIVO.format(p)) for p in PROPIEDADES])
    muestra = imagen.sample(ee.Geometry.Point([lon, lat]), ESCALA_M).first()
    valores = muestra.toDictionary().getInfo() if muestra else {}
    capas = []
    for prop, (d_factor, unidades) in PROPIEDADES.items():
        profundidades = []
        for etiqueta in PROFUNDIDADES:
            v = valores.get(f'{prop}_{etiqueta}_mean')
            arriba, abajo = _rango(etiqueta)
            profundidades.append({'label': etiqueta, 'range': {'top_depth': arriba, 'bottom_depth': abajo},
                                  'values': {'mean': v, 'Q0.5': v}})
        capas.append({'name': prop, 'unit_measure': {'d_factor': d_factor, 'mapped_units': '', 'target_units': unidades},
                      'depths': profundidades})
    return {'properties': {'layers': capas}}
