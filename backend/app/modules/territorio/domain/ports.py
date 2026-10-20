from typing import Protocol

from app.modules.territorio.domain.entity import Municipio


class TerritorioRepository(Protocol):
    def municipios(self, departamento: str) -> list[Municipio] | None:
        """None si el departamento no está cargado; lista vacía no ocurre."""
        ...

    def municipio(self, codigo: str) -> Municipio | None:
        ...

    def todos(self) -> list[Municipio]:
        """Todos los municipios cargados, de cualquier departamento."""
        ...


class ModeloElevacion(Protocol):
    fuente: str

    async def altitud(self, lat: float, lon: float) -> float | None:
        """Metros sobre el nivel del mar, o None si el modelo no tiene dato para el punto."""
        ...
