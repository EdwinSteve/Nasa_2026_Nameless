import json
from functools import lru_cache
from pathlib import Path

from app.modules.territorio.domain.entity import CentroPoblado, Municipio

# Generado con scripts/actualizar_divipola.py: cambia muy poco y se versiona con el código.
ARCHIVO = Path(__file__).parent / "datos" / "divipola.json"


class DivipolaJsonRepository:
    """Lee DIVIPOLA una sola vez desde el JSON del repositorio y lo deja en memoria."""

    def __init__(self, archivo: Path = ARCHIVO) -> None:
        self._por_departamento, self._por_codigo = _cargar(archivo)

    def municipios(self, departamento: str) -> list[Municipio] | None:
        return self._por_departamento.get(departamento)

    def municipio(self, codigo: str) -> Municipio | None:
        return self._por_codigo.get(codigo)

    def todos(self) -> list[Municipio]:
        return list(self._por_codigo.values())


@lru_cache
def _cargar(archivo: Path) -> tuple[dict[str, list[Municipio]], dict[str, Municipio]]:
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    por_departamento: dict[str, list[Municipio]] = {}
    for depto in datos["departamentos"]:
        por_departamento[depto["codigo"]] = [
            Municipio(
                codigo=m["codigo"],
                nombre=m["nombre"],
                departamento=depto["codigo"],
                lat=m.get("lat"),
                lon=m.get("lon"),
                centros_poblados=tuple(CentroPoblado(**c) for c in m["centros_poblados"]),
            )
            for m in depto["municipios"]
        ]
    por_codigo = {m.codigo: m for lista in por_departamento.values() for m in lista}
    return por_departamento, por_codigo
