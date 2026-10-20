from app.modules.territorio.domain.entity import CentroPoblado, Municipio
from app.modules.territorio.domain.errors import DepartamentoNoDisponible, MunicipioNoEncontrado
from app.modules.territorio.domain.ports import TerritorioRepository


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
