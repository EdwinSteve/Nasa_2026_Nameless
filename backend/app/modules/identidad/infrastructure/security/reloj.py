from datetime import datetime, timezone


class RelojSistema:
    """Reloj real en UTC. Las pruebas usan un reloj falso que implementa el mismo puerto Clock."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)
