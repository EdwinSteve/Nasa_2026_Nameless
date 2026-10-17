import hashlib
import secrets


class GeneradorRefreshToken:
    """Genera refresh tokens opacos y calcula su hash SHA-256.

    El token se entrega una sola vez al cliente. En la base de datos solo
    se guarda el hash, así que una filtración de la tabla no permite usar sesiones.
    """

    BYTES_ALEATORIOS = 32

    def generar(self) -> str:
        return secrets.token_urlsafe(self.BYTES_ALEATORIOS)

    def hashear(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
