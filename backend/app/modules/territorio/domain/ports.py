from typing import Protocol

from app.modules.territorio.domain.entity import Municipio


class TerritorioRepository(Protocol):
    def municipios(self, departamento: str) -> list[Municipio] | None:
        """None si el departamento no está cargado; lista vacía no ocurre."""
        ...

    def municipio(self, codigo: str) -> Municipio | None:
        ...
