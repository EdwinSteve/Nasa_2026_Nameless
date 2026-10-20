from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt

from app.core.config import get_settings


class JwtTokenIssuer:
    """Emite y valida access tokens JWT firmados con HS256.

    El payload solo lleva identificadores (sub, rol, jti) y metadatos del token.
    Nunca incluye celular, nombre ni otros datos personales: el JWT se puede
    decodificar aunque no se pueda falsificar.
    """

    def __init__(self) -> None:
        s = get_settings()
        self._secret = s.jwt_secreto.get_secret_value()
        self._alg = s.jwt_algoritmo
        self._iss = s.jwt_emisor
        self._aud = s.jwt_audiencia
        self._access_min = s.jwt_access_minutos

    @property
    def duracion_segundos(self) -> int:
        return self._access_min * 60

    def issue_access_token(self, user_id: UUID, rol: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "rol": rol,
            "iss": self._iss,
            "aud": self._aud,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self._access_min)).timestamp()),
            "jti": str(uuid4()),
        }
        return jwt.encode(payload, self._secret, algorithm=self._alg)

    def decode_access_token(self, token: str) -> dict:
        return jwt.decode(
            token,
            self._secret,
            algorithms=[self._alg],
            audience=self._aud,
            issuer=self._iss,
            options={"require": ["sub", "rol", "iss", "aud", "iat", "exp", "jti"]},
        )
