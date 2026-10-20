from functools import lru_cache

from app.modules.territorio.application.consultas import ConsultarTerritorio
from app.modules.territorio.infrastructure.divipola_json import DivipolaJsonRepository


@lru_cache
def get_consultar_territorio() -> ConsultarTerritorio:
    """El catálogo vive en memoria: una sola instancia para toda la app."""
    return ConsultarTerritorio(territorio=DivipolaJsonRepository())
