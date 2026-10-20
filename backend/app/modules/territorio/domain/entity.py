from dataclasses import dataclass, field


@dataclass(frozen=True)
class CentroPoblado:
    """Cabecera municipal (tipo CM) o centro poblado rural (CP) de DIVIPOLA.

    DIVIPOLA no publica la figura de "corregimiento"; el centro poblado es la unidad
    rural oficial más cercana y es la que la UI muestra en ese campo.
    """

    codigo: str          # 8 dígitos DANE: municipio (5) + centro poblado (3)
    nombre: str
    tipo: str            # "CM" o "CP"
    lat: float | None = None
    lon: float | None = None

    @property
    def es_cabecera(self) -> bool:
        return self.tipo == "CM"


@dataclass(frozen=True)
class Municipio:
    codigo: str          # 5 dígitos DANE
    nombre: str
    departamento: str    # 2 dígitos DANE
    lat: float | None = None
    lon: float | None = None
    centros_poblados: tuple[CentroPoblado, ...] = field(default=())


@dataclass(frozen=True)
class Elevacion:
    altitud_msnm: float
    fuente: str
    municipio: Municipio | None   # el más cercano en DIVIPOLA; None si el punto queda lejos de todos
