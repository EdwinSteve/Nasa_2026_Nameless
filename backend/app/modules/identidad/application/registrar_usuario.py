from datetime import timedelta
from uuid import uuid4

from app.modules.identidad.application.dto import DatosRegistro, ParTokens, ResultadoRegistro
from app.modules.identidad.domain.entity import Role, Sesion, User, UserStatus
from app.modules.identidad.domain.errors import (
    ConsentRequired,
    EmailAlreadyRegistered,
    PhoneAlreadyRegistered,
    PolicyOutdated,
)
from app.modules.identidad.domain.ports import (
    Clock,
    ConsentimientoRepository,
    EventoRepository,
    GeneradorRefresh,
    Hasher,
    PoliticaRepository,
    SesionRepository,
    TokenIssuer,
    UnitOfWork,
    UserRepository,
)
from app.modules.identidad.domain.values import Email, Phone


class RegistrarUsuario:
    """Caso de uso ID-03: registro de productor.

    Usuario, consentimiento, sesión y evento se guardan en una sola transacción
    (un único `uow.confirmar()` al final): o se guarda todo, o nada.
    La contraseña solo existe en claro dentro de este método; nunca se registra.
    """

    def __init__(
            self,
            *,
            usuarios: UserRepository,
            politicas: PoliticaRepository,
            consentimientos: ConsentimientoRepository,
            sesiones: SesionRepository,
            eventos: EventoRepository,
            hasher: Hasher,
            tokens: TokenIssuer,
            generador: GeneradorRefresh,
            reloj: Clock,
            uow: UnitOfWork,
            dias_refresh: int,
    ) -> None:
        self._usuarios = usuarios
        self._politicas = politicas
        self._consentimientos = consentimientos
        self._sesiones = sesiones
        self._eventos = eventos
        self._hasher = hasher
        self._tokens = tokens
        self._generador = generador
        self._reloj = reloj
        self._uow = uow
        self._dias_refresh = dias_refresh

    async def ejecutar(self, datos: DatosRegistro) -> ResultadoRegistro:
        if not datos.accepts_policy:
            raise ConsentRequired()
        politica = await self._politicas.get_active()
        if politica is None or politica.version != datos.policy_version:
            raise PolicyOutdated()

        ahora = self._reloj.now()
        phone = Phone.desde_entrada(datos.phone, solo_movil=True)
        email = Email(datos.email) if datos.email else None

        if await self._usuarios.get_by_phone(phone.value) is not None:
            raise PhoneAlreadyRegistered()
        if email is not None and await self._usuarios.get_by_email(email.value) is not None:
            raise EmailAlreadyRegistered()

        usuario = User(
            phone=phone,
            email=email,
            password_hash=self._hasher.generate_hash(datos.password),
            role=Role.PRODUCTOR,
            status=UserStatus.ACTIVE,
            full_name=datos.full_name,
            municipality=datos.municipality,
            district=datos.district,
        )
        usuario = await self._usuarios.save(usuario)
        await self._consentimientos.registrar(usuario.id, politica.id, ahora)

        refresh = self._generador.generar()
        await self._sesiones.crear(
            Sesion(
                user_id=usuario.id,
                token_hash=self._generador.hashear(refresh),
                family_id=uuid4(),
                expires_at=ahora + timedelta(days=self._dias_refresh),
            )
        )
        await self._eventos.registrar("registro", usuario.id)
        await self._uow.confirmar()

        return ResultadoRegistro(
            usuario=usuario,
            tokens=ParTokens(
                access_token=self._tokens.issue_access_token(usuario.id, usuario.role.value),
                refresh_token=refresh,
                expira_en=self._tokens.duracion_segundos,
            ),
        )