from functools import lru_cache

from app.modules.territorio.application.consultas import ConsultarElevacion, ConsultarTerritorio
from app.modules.territorio.infrastructure.divipola_json import DivipolaJsonRepository
from app.modules.territorio.infrastructure.elevacion_srtm import ElevacionSRTM


@lru_cache
def get_consultar_territorio() -> ConsultarTerritorio:
    """El catálogo vive en memoria: una sola instancia para toda la app."""
    return ConsultarTerritorio(territorio=DivipolaJsonRepository())


@lru_cache
def get_consultar_elevacion() -> ConsultarElevacion:
    """Una sola instancia para que la caché de elevaciones sirva a todas las peticiones."""
    return ConsultarElevacion(territorio=DivipolaJsonRepository(), modelo=ElevacionSRTM())
