from anyio.functools import lru_cache
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
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

@lru_cache
def get_settings() -> Settings:
    return Settings()
