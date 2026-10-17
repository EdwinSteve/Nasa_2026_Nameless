from dataclasses import dataclass


@dataclass(frozen=True)
class ParTokens:
    """Resultado de un login o de un refresh: un access token y su refresh token nuevo."""

    access_token: str
    refresh_token: str
    expira_en: int
    token_type: str = "bearer"
