from datetime import timedelta

from app.modules.identidad.application.dto import ParTokens
from app.modules.identidad.domain.entity import Sesion, UserStatus
from app.modules.identidad.domain.errors import RefreshTokenInvalid
from app.modules.identidad.domain.ports import (
    Clock,
    EventoRepository,
    GeneradorRefresh,
    SesionRepository,
    TokenIssuer,
    UnitOfWork,
    UserRepository,
)


class RefrescarSesion:
    """Caso de uso ID-05: rota el refresh token y devuelve un par nuevo.

    Cada refresh token sirve una sola vez. Si llega uno ya usado, se asume robo:
    se revoca toda la familia (todas las sesiones derivadas de ese login).
    La búsqueda usa FOR UPDATE, así dos peticiones simultáneas con el mismo token
    no pueden generar dos sesiones válidas.
    """

    def __init__(
        self,
        *,
        usuarios: UserRepository,
        sesiones: SesionRepository,
        eventos: EventoRepository,
        tokens: TokenIssuer,
        generador: GeneradorRefresh,
        reloj: Clock,
        uow: UnitOfWork,
        dias_refresh: int,
    ) -> None:
        self._usuarios = usuarios
        self._sesiones = sesiones
        self._eventos = eventos
        self._tokens = tokens
        self._generador = generador
        self._reloj = reloj
        self._uow = uow
        self._dias_refresh = dias_refresh

    async def ejecutar(self, refresh_token: str) -> ParTokens:
        ahora = self._reloj.now()
        actual = await self._sesiones.buscar_por_hash_para_actualizar(
            self._generador.hashear(refresh_token)
        )

        if actual is None or actual.revocada or actual.expirada(ahora):
            raise RefreshTokenInvalid()

        if actual.usada:
            await self._sesiones.revocar_familia(actual.family_id, ahora)
            await self._eventos.registrar("refresh", actual.user_id, {"motivo": "reutilizado"})
            await self._uow.confirmar()
            raise RefreshTokenInvalid()

        usuario = await self._usuarios.get_by_id(actual.user_id)
        if usuario is None or usuario.status == UserStatus.INACTIVE or usuario.is_blocked(ahora):
            raise RefreshTokenInvalid()

        nuevo_refresh = self._generador.generar()
        sesion_nueva = Sesion(
            user_id=usuario.id,
            token_hash=self._generador.hashear(nuevo_refresh),
            family_id=actual.family_id,
            expires_at=ahora + timedelta(days=self._dias_refresh),
        )
        # El orden importa: la sesión nueva debe existir antes de que la anterior apunte a ella.
        await self._sesiones.crear(sesion_nueva)
        await self._sesiones.marcar_usada(actual.id, sesion_nueva.id, ahora)
        await self._eventos.registrar("refresh", usuario.id)
        await self._uow.confirmar()

        return ParTokens(
            access_token=self._tokens.issue_access_token(usuario.id, usuario.role.value),
            refresh_token=nuevo_refresh,
            expira_en=self._tokens.duracion_segundos,
        )
