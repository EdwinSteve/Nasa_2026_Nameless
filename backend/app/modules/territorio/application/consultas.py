import math

from app.modules.territorio.domain.entity import CentroPoblado, Elevacion, Municipio
from app.modules.territorio.domain.errors import (
    DepartamentoNoDisponible,
    ElevacionNoDisponible,
    MunicipioNoEncontrado,
)
from app.modules.territorio.domain.ports import ModeloElevacion, TerritorioRepository


class ConsultarTerritorio:
    """Catálogo DIVIPOLA de solo lectura. Lo usan la UI (listas del registro) y el
    módulo fincas (validar el municipio y el centro poblado de una finca)."""

    def __init__(self, *, territorio: TerritorioRepository) -> None:
        self._territorio = territorio

    def municipios(self, departamento: str) -> list[Municipio]:
        lista = self._territorio.municipios(departamento)
        if lista is None:
            raise DepartamentoNoDisponible(departamento)
        return lista

    def municipio(self, codigo: str) -> Municipio:
        municipio = self._territorio.municipio(codigo)
        if municipio is None:
            raise MunicipioNoEncontrado(codigo)
        return municipio

    def centros_poblados(self, municipio: str) -> list[CentroPoblado]:
        return list(self.municipio(municipio).centros_poblados)

    def centro_poblado(self, municipio: str, codigo: str) -> CentroPoblado | None:
        return next((c for c in self.centros_poblados(municipio) if c.codigo == codigo), None)


# Si el centro poblado más cercano está a más de esto, el punto no se asigna a ningún municipio:
# sin polígonos municipales, más lejos el nombre podría ser el de un municipio vecino.
DISTANCIA_MAXIMA_KM = 15.0


def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine sobre una esfera de 6371 km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat, dlon = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


class ConsultarElevacion:
    """Altitud de un punto (modelo de elevación) y el municipio al que más probablemente pertenece.

    El municipio se aproxima por el casco urbano o centro poblado DIVIPOLA más cercano.
    """

    def __init__(self, *, territorio: TerritorioRepository, modelo: ModeloElevacion) -> None:
        self._territorio = territorio
        self._modelo = modelo

    def municipio_cercano(self, lat: float, lon: float) -> Municipio | None:
        mejor, mejor_km = None, DISTANCIA_MAXIMA_KM
        for m in self._territorio.todos():
            puntos = [(m.lat, m.lon)] + [(c.lat, c.lon) for c in m.centros_poblados]
            for plat, plon in puntos:
                if plat is None or plon is None:
                    continue
                km = distancia_km(lat, lon, plat, plon)
                if km < mejor_km:
                    mejor, mejor_km = m, km
        return mejor

    async def ejecutar(self, lat: float, lon: float) -> Elevacion:
        try:
            altitud = await self._modelo.altitud(lat, lon)
        except Exception as exc:  # red caída, límite de la API, respuesta inesperada
            raise ElevacionNoDisponible() from exc
        if altitud is None:
            raise ElevacionNoDisponible()
        return Elevacion(altitud_msnm=altitud, fuente=self._modelo.fuente, municipio=self.municipio_cercano(lat, lon))
