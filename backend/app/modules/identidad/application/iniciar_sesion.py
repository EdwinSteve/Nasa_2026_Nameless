from datetime import timedelta
from uuid import uuid4

from app.modules.identidad.application.dto import ParTokens
from app.modules.identidad.domain.entity import Sesion, UserStatus
from app.modules.identidad.domain.errors import InvalidPhone, InvalidCredentials, UserBlocked
from app.modules.identidad.domain.ports import (
    Clock,
    EventoRepository,
    GeneradorRefresh,
    Hasher,
    SesionRepository,
    TokenIssuer,
    UnitOfWork,
    UserRepository,
)
from app.modules.identidad.domain.values import Phone


class IniciarSesion:
    """Caso de uso ID-04: login con celular y contraseña.

    Reglas:
    - Celular inexistente y contraseña incorrecta responden exactamente igual (401).
    - Cada intento se compara contra un hash, también si el celular no existe, para que
      el tiempo de respuesta no revele qué celulares están registrados.
    - Tras `max_intentos` fallos seguidos, la cuenta queda bloqueada `bloqueo_minutos`.
    - Un login exitoso reinicia el contador de intentos.
    """

    def __init__(
        self,
        *,
        usuarios: UserRepository,
        sesiones: SesionRepository,
        eventos: EventoRepository,
        hasher: Hasher,
        hash_ficticio: str,
        tokens: TokenIssuer,
        generador: GeneradorRefresh,
        reloj: Clock,
        uow: UnitOfWork,
        max_intentos: int,
        bloqueo_minutos: int,
        dias_refresh: int,
    ) -> None:
        self._usuarios = usuarios
        self._sesiones = sesiones
        self._eventos = eventos
        self._hasher = hasher
        self._hash_ficticio = hash_ficticio
        self._tokens = tokens
        self._generador = generador
        self._reloj = reloj
        self._uow = uow
        self._max_intentos = max_intentos
        self._bloqueo_minutos = bloqueo_minutos
        self._dias_refresh = dias_refresh

    async def ejecutar(self, celular: str, contrasena: str) -> ParTokens:
        ahora = self._reloj.now()
        usuario = await self._buscar_usuario(celular)

        if usuario is None:
            self._hasher.verify_hash(contrasena, self._hash_ficticio)
            raise InvalidCredentials()

        if usuario.is_blocked(ahora):
            self._hasher.verify_hash(contrasena, self._hash_ficticio)
            raise UserBlocked()

        if usuario.locked_until is not None:
            # El bloqueo ya venció: se libera la cuenta en el primer intento posterior.
            usuario.reiniciar_intentos()
            await self._eventos.registrar("desbloqueo", usuario.id)

        if usuario.status == UserStatus.INACTIVE:
            # "Eliminado" en el issue: mismo error genérico que una contraseña incorrecta.
            self._hasher.verify_hash(contrasena, self._hash_ficticio)
            raise InvalidCredentials()

        if not self._hasher.verify_hash(contrasena, usuario.password_hash):
            bloqueada = usuario.registrar_fallo(ahora, self._max_intentos, self._bloqueo_minutos)
            await self._eventos.registrar("login_fallido", usuario.id)
            if bloqueada:
                await self._eventos.registrar("bloqueo", usuario.id)
            await self._usuarios.save(usuario)
            await self._uow.confirmar()
            raise InvalidCredentials()

        if self._hasher.necesita_rehash(usuario.password_hash):
            usuario.password_hash = self._hasher.generate_hash(contrasena)

        usuario.registrar_login(ahora)
        refresh = self._generador.generar()
        sesion = Sesion(
            user_id=usuario.id,
            token_hash=self._generador.hashear(refresh),
            family_id=uuid4(),
            expires_at=ahora + timedelta(days=self._dias_refresh),
        )
        await self._sesiones.crear(sesion)
        await self._usuarios.save(usuario)
        await self._eventos.registrar("login_exitoso", usuario.id)
        await self._uow.confirmar()

        return ParTokens(
            access_token=self._tokens.issue_access_token(usuario.id, usuario.role.value),
            refresh_token=refresh,
            expira_en=self._tokens.duracion_segundos,
        )

    async def _buscar_usuario(self, celular: str):
        try:
            e164 = Phone.desde_entrada(celular).value
        except InvalidPhone:
            return None
        return await self._usuarios.get_by_phone(e164)
