from uuid import UUID

from app.modules.identidad.domain.ports import (
    Clock,
    EventoRepository,
    GeneradorRefresh,
    SesionRepository,
    UnitOfWork,
)


class CerrarSesion:
    """Caso de uso ID-06: cerrar una sesión o todas las del usuario.

    El access token no se revoca: deja de servir cuando caduca (máximo 15 minutos).
    Por eso el cierre revoca el refresh token, que es lo que permite renovar.
    """

    def __init__(
        self,
        *,
        sesiones: SesionRepository,
        eventos: EventoRepository,
        generador: GeneradorRefresh,
        reloj: Clock,
        uow: UnitOfWork,
    ) -> None:
        self._sesiones = sesiones
        self._eventos = eventos
        self._generador = generador
        self._reloj = reloj
        self._uow = uow

    async def una(self, usuario_id: UUID, refresh_token: str) -> None:
        """Revoca la sesión de ese refresh token.

        Es idempotente. Si el token ya estaba revocado, no existe, o pertenece a otro
        usuario, no pasa nada y no se revela cuál de los casos fue.
        """
        ahora = self._reloj.now()
        sesion = await self._sesiones.buscar_por_hash(self._generador.hashear(refresh_token))
        if sesion is None or sesion.user_id != usuario_id or sesion.revocada:
            return

        await self._sesiones.revocar(sesion.id, ahora)
        await self._eventos.registrar("logout", usuario_id, {"alcance": "una"})
        await self._uow.confirmar()

    async def todas(self, usuario_id: UUID) -> None:
        """Revoca todas las sesiones activas del usuario, en todos sus dispositivos."""
        ahora = self._reloj.now()
        await self._sesiones.revocar_todas_del_usuario(usuario_id, ahora)
        await self._eventos.registrar("logout", usuario_id, {"alcance": "todas"})
        await self._uow.confirmar()
