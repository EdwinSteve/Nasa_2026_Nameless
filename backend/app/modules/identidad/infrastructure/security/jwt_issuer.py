from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from app.core.config import get_settings


class JwtTokenIssuer:
    def __init__(self) -> None:
        s = get_settings()
        self._secret = s.jwt_secreto.get_secret_value()
        self._alg = s.jwt_algoritmo
        self._iss = s.jwt_emisor
        self._aud = s.jwt_audiencia
        self._access_min = s.jwt_access_minutos

    def issue_access_token(self, user_id: UUID, role: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "role": role,
            "iss": self._iss,
            "aud": self._aud,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self._access_min)).timestamp()),
        }
        return jwt.encode(payload, self._secret, algorithm=self._alg)

    def decode_access_token(self, token: str) -> dict:
        return jwt.decode(
            token,
            self._secret,
            algorithms=[self._alg],
            audience=self._aud,
            issuer=self._iss,
        )