from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from app.modules.fincas.domain.values import Poligono


class TipoRiego(str, Enum):
    GRAVEDAD = "gravedad"
    ASPERSION = "aspersion"
    GOTEO = "goteo"


class Prioridad(str, Enum):
    AHORRO_AGUA = "ahorro_agua"
    GANAR_MAS = "ganar_mas"
    CUIDAR_SUELO = "cuidar_suelo"
    ARRIESGAR_MENOS = "arriesgar_menos"


@dataclass
class Finca:
    propietario_id: UUID
    nombre: str
    municipio: str                 # código DIVIPOLA (5 dígitos)
    centro_poblado: str            # código DIVIPOLA (8 dígitos)
    vereda: str | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime | None = None


@dataclass
class Lote:
    finca_id: UUID
    nombre: str
    poligono: Poligono
    tiene_riego: bool
    tipo_riego: TipoRiego | None = None
    cultivo_anterior: str | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime | None = None

    @property
    def area_ha(self) -> float:
        return round(self.poligono.area_ha, 4)


@dataclass(frozen=True)
class Preferencias:
    """Orden de lo que más le importa al productor: lo usa el motor para pesar el MCDA."""

    usuario_id: UUID
    orden: tuple[Prioridad, ...]
