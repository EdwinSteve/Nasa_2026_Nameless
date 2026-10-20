from functools import lru_cache
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Database
    database_url: str = Field(min_length=1)

    # JWT
    jwt_secreto: SecretStr = Field(min_length=64)
    jwt_algoritmo: str = "HS256"
    jwt_emisor: str = "surco-api"
    jwt_audiencia: str = "surco-app"
    jwt_access_minutos: int = Field(default=15, gt=0)

    # Refresh tokens
    refresh_dias: int = Field(default=30, gt=0)

    # Login
    login_max_intentos: int = Field(default=5, gt=0)
    login_bloqueo_minutos: int = Field(default=15, gt=0)

    # Frontend
    # Orígenes que pueden llamar a la API desde el navegador, separados por comas.
    cors_origenes: str = "http://localhost:3000"
    # Dónde lee el productor el texto completo de la política (una ruta de la UI).
    politica_url: str = "/politica-de-datos"

    # Diagnóstico satelital (datos_tierra). Sin proyecto de Earth Engine, la humedad
    # (SMAP) y el verdor (MODIS) quedan como pasos fallidos; clima y suelo funcionan igual.
    gee_project: str | None = None

    @property
    def cors_origenes_lista(self) -> list[str]:
        return [o.strip() for o in self.cors_origenes.split(",") if o.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings() # type: ignore[call-arg]
