"""Dobles en memoria para los puertos del módulo fincas."""

from uuid import UUID

# Polígono de ~6,4 ha en Fortalecillas (Neiva), en orden [lon, lat]
POLIGONO = {
    "type": "Polygon",
    "coordinates": [[
        [-75.2941, 2.9912],
        [-75.2895, 2.9920],
        [-75.2882, 2.9865],
        [-75.2930, 2.9858],
        [-75.2941, 2.9912],
    ]],
}
NEIVA, FORTALECILLAS = "41001", "41001003"


class FincasFalsas:
    def __init__(self) -> None:
        self.por_id: dict = {}

    async def crear(self, finca):
        self.por_id[finca.id] = finca
        return finca

    async def obtener(self, finca_id: UUID):
        return self.por_id.get(finca_id)


class LotesFalsos(FincasFalsas):
    pass


class PreferenciasFalsas:
    def __init__(self) -> None:
        self.por_usuario: dict = {}

    async def guardar(self, preferencias) -> None:
        self.por_usuario[preferencias.usuario_id] = preferencias


class TerritorioFalso:
    def nombres(self, municipio: str, centro_poblado: str):
        if (municipio, centro_poblado) == (NEIVA, FORTALECILLAS):
            return "Neiva", "Fortalecillas"
        return None


class UnitOfWorkFalso:
    def __init__(self) -> None:
        self.confirmaciones = 0

    async def confirmar(self) -> None:
        self.confirmaciones += 1
