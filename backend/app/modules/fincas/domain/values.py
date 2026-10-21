from __future__ import annotations

import math
from dataclasses import dataclass

from app.modules.fincas.domain.errors import PoligonoInvalido

RADIO_TIERRA_M = 6_371_008.8
# Caja de Colombia continental e insular (San Andrés incluido), con margen.
LON_MIN, LON_MAX = -82.5, -66.0
LAT_MIN, LAT_MAX = -4.5, 13.5
AREA_MIN_HA = 0.01      # 100 m²: por debajo casi seguro es un error al dibujar
AREA_MAX_HA = 5_000.0   # un lote, no una vereda
VERTICES_MAX = 500


@dataclass(frozen=True)
class Poligono:
    """Polígono GeoJSON (EPSG:4326) de un lote: un solo anillo exterior, sin huecos.

    Las coordenadas van en orden GeoJSON: [longitud, latitud].
    """

    anillo: tuple[tuple[float, float], ...]

    @classmethod
    def desde_geojson(cls, geojson: dict) -> Poligono:
        if not isinstance(geojson, dict) or geojson.get("type") != "Polygon":
            raise PoligonoInvalido("El lote debe ser un polígono GeoJSON (type = Polygon).")
        anillos = geojson.get("coordinates")
        if not isinstance(anillos, list) or len(anillos) != 1:
            raise PoligonoInvalido("El lote debe tener un solo borde exterior, sin huecos.")
        try:
            anillo = tuple((float(p[0]), float(p[1])) for p in anillos[0])
        except (TypeError, ValueError, IndexError) as exc:
            raise PoligonoInvalido("Cada esquina debe ser [longitud, latitud].") from exc
        return cls(anillo)

    def __post_init__(self) -> None:
        if len(self.anillo) < 4:
            raise PoligonoInvalido("El lote necesita al menos 3 esquinas.")
        if len(self.anillo) > VERTICES_MAX + 1:
            raise PoligonoInvalido(f"El lote puede tener como máximo {VERTICES_MAX} esquinas.")
        if self.anillo[0] != self.anillo[-1]:
            raise PoligonoInvalido("El borde del lote debe cerrarse: la última esquina repite la primera.")
        for lon, lat in self.anillo:
            if not (LON_MIN <= lon <= LON_MAX and LAT_MIN <= lat <= LAT_MAX):
                raise PoligonoInvalido("El lote está fuera de Colombia. Revise si invirtió la latitud y la longitud.")
        if len(set(self.anillo[:-1])) < 3:
            raise PoligonoInvalido("El lote necesita al menos 3 esquinas distintas.")
        if _se_cruza(self.anillo):
            raise PoligonoInvalido("El borde del lote se cruza consigo mismo. Marque las esquinas en orden.")
        area = self.area_ha
        if area < AREA_MIN_HA:
            raise PoligonoInvalido("El lote es demasiado pequeño (menos de 100 m²).")
        if area > AREA_MAX_HA:
            raise PoligonoInvalido(f"El lote es demasiado grande (más de {AREA_MAX_HA:,.0f} ha).")

    @property
    def vertices(self) -> tuple[tuple[float, float], ...]:
        return self.anillo[:-1]

    @property
    def area_ha(self) -> float:
        """Área sobre la esfera (Chamberlain y Duquette, 2007): exacta para un lote."""
        suma = 0.0
        for (lon1, lat1), (lon2, lat2) in zip(self.anillo, self.anillo[1:]):
            suma += math.radians(lon2 - lon1) * (2 + math.sin(math.radians(lat1)) + math.sin(math.radians(lat2)))
        return abs(suma) * RADIO_TIERRA_M**2 / 2 / 10_000

    @property
    def centroide(self) -> tuple[float, float]:
        """(lat, lon) del punto medio del lote: el centroide ponderado por área.

        Promediar las esquinas desplaza el centro hacia donde hay más puntos marcados (un borde
        curvo con muchas esquinas lo jala); el centroide de área no depende de cuántas esquinas
        tenga cada lado. Se calcula en una proyección local en metros, exacta para un lote.
        En un lote muy cóncavo (en forma de C) puede caer fuera del polígono.
        """
        lons, lats = zip(*self.vertices)
        lat0 = math.radians(sum(lats) / len(lats))
        lon_ref, lat_ref = lons[0], lats[0]
        escala_x = math.radians(1) * RADIO_TIERRA_M * math.cos(lat0)
        escala_y = math.radians(1) * RADIO_TIERRA_M
        puntos = [((lon - lon_ref) * escala_x, (lat - lat_ref) * escala_y) for lon, lat in self.anillo]

        area2 = cx = cy = 0.0
        for (x1, y1), (x2, y2) in zip(puntos, puntos[1:]):
            cruz = x1 * y2 - x2 * y1
            area2 += cruz
            cx += (x1 + x2) * cruz
            cy += (y1 + y2) * cruz
        cx, cy = cx / (3 * area2), cy / (3 * area2)
        return round(lat_ref + cy / escala_y, 6), round(lon_ref + cx / escala_x, 6)

    def a_geojson(self) -> dict:
        return {"type": "Polygon", "coordinates": [[list(p) for p in self.anillo]]}


def _orientacion(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _segmentos_se_cruzan(p1, p2, p3, p4) -> bool:
    """Cruce propio (no cuenta tocarse en un extremo compartido)."""
    d1, d2 = _orientacion(p3, p4, p1), _orientacion(p3, p4, p2)
    d3, d4 = _orientacion(p1, p2, p3), _orientacion(p1, p2, p4)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and 0 not in (d1, d2, d3, d4)


def _se_cruza(anillo) -> bool:
    lados = list(zip(anillo, anillo[1:]))
    n = len(lados)
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:  # el primer y el último lado comparten la esquina inicial
                continue
            if _segmentos_se_cruzan(*lados[i], *lados[j]):
                return True
    return False
