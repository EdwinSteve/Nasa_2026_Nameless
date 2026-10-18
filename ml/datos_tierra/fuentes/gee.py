"""Utilidades comunes de Google Earth Engine.

`ee` se importa dentro de las funciones para que el paquete funcione sin
earthengine-api cuando solo se usan POWER, SoilGrids, DEM y ENSO.
"""
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

# getInfo() admite hasta 5000 elementos; 1000 días por bloque deja margen y
# evita los tiempos de espera del servidor en series largas.
DIAS_POR_BLOQUE = 1000
HILOS = 4

_inicializado = False


class FuenteOmitida(Exception):
    """La fuente no se consultó por falta de configuración (no es un fallo de la API)."""


def inicializar() -> None:
    global _inicializado
    if _inicializado:
        return
    proyecto = os.environ.get('GEE_PROJECT')
    if not proyecto:
        raise FuenteOmitida('Falta la variable GEE_PROJECT (y autenticar con ee.Authenticate()).')
    try:
        import ee
    except ImportError as exc:
        raise FuenteOmitida('Falta instalar earthengine-api.') from exc
    ee.Initialize(project=proyecto)
    _inicializado = True


def region(lat: float, lon: float, poligono: list[list[float]] | None, buffer_m: float):
    """poligono: lista de [lon, lat]. Sin polígono se usa un buffer alrededor del punto."""
    import ee
    if poligono:
        return ee.Geometry.Polygon([poligono])
    return ee.Geometry.Point([lon, lat]).buffer(buffer_m)


def recortar(inicio: date, fin: date, disponible_desde: date) -> tuple[date, date] | None:
    """Ajusta el rango al inicio de la misión. None si el rango queda vacío."""
    inicio = max(inicio, disponible_desde)
    return (inicio, fin) if inicio <= fin else None


def bloques(inicio: date, fin: date, dias: int = DIAS_POR_BLOQUE) -> list[tuple[date, date]]:
    salida, a = [], inicio
    while a <= fin:
        b = min(a + timedelta(days=dias - 1), fin)
        salida.append((a, b))
        a = b + timedelta(days=1)
    return salida


def serie_diaria(
    imagen_del_dia: Callable,
    geometria,
    inicio: date,
    fin: date,
    escala_m: float,
) -> list[dict]:
    """Promedio espacial diario sobre la geometría.

    imagen_del_dia(dia: ee.Date) -> (ee.Image, ee.Number con el número de imágenes del día).
    Devuelve una fila por día con 'date', 'n_img' y las bandas de la imagen.
    """
    import ee

    def un_bloque(rango: tuple[date, date]) -> list[dict]:
        a, b = rango
        t0 = ee.Date(a.isoformat())

        def por_dia(i):
            dia = t0.advance(ee.Number(i), 'day')
            imagen, n_img = imagen_del_dia(dia)
            stats = imagen.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geometria,
                scale=escala_m,
                maxPixels=1e9,
            )
            return ee.Feature(None, stats).set({'date': dia.format('YYYY-MM-dd'), 'n_img': n_img})

        fc = ee.FeatureCollection(ee.List.sequence(0, (b - a).days).map(por_dia))
        return [f['properties'] for f in fc.getInfo()['features']]

    with ThreadPoolExecutor(HILOS) as ejecutor:
        partes = list(ejecutor.map(un_bloque, bloques(inicio, fin)))
    return [fila for parte in partes for fila in parte]
