from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError


class Argon2Hasher:
    def __init__(self) -> None:
        self._ph = PasswordHasher()

    def generate_hash(self, value: str) -> str:
        return self._ph.hash(value)

    def verify_hash(self, value: str, hash_storage: str) -> bool:
        try:
            return self._ph.verify(hash_storage, value)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    def necesita_rehash(self, hash_storage: str) -> bool:
        """True si el hash fue creado con parámetros anteriores y conviene recalcularlo."""
        return self._ph.check_needs_rehash(hash_storage)