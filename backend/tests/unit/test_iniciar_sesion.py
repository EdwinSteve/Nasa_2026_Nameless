from datetime import datetime, timedelta, timezone

import pytest

from app.modules.identidad.application.iniciar_sesion import IniciarSesion
from app.modules.identidad.domain.entity import Role, User, UserStatus
from app.modules.identidad.domain.errors import InvalidCredentials, UserBlocked
from app.modules.identidad.domain.values import Email, Phone
from tests.unit.fakes import (
    EventosFalsos,
    GeneradorFalso,
    HasherFalso,
    RelojFalso,
    SesionesFalsas,
    TokensFalsos,
    UnitOfWorkFalso,
    UsuariosFalsos,
)

CELULAR_E164 = "+573001234567"
CONTRASENA = "MiFinca2026"
AHORA = datetime(2026, 10, 17, 10, 0, tzinfo=timezone.utc)


class Entorno:
    """Agrupa un caso de uso con sus dobles para poder inspeccionarlos en cada prueba."""

    def __init__(self, necesita_rehash: bool = False) -> None:
        self.usuarios = UsuariosFalsos()
        self.sesiones = SesionesFalsas()
        self.eventos = EventosFalsos()
        self.reloj = RelojFalso(AHORA)
        self.uow = UnitOfWorkFalso()
        self.hasher = HasherFalso(necesita_rehash=necesita_rehash)
        self.usuario = User(
            phone=Phone(CELULAR_E164),
            email=Email("ana@finca.co"),
            password_hash=self.hasher.generate_hash(CONTRASENA),
            role=Role.APRENDIZ,
            status=UserStatus.ACTIVE,
        )
        self.usuarios.agregar(self.usuario)
        self.caso = IniciarSesion(
            usuarios=self.usuarios,
            sesiones=self.sesiones,
            eventos=self.eventos,
            hasher=self.hasher,
            hash_ficticio=self.hasher.generate_hash("valor-ficticio"),
            tokens=TokensFalsos(),
            generador=GeneradorFalso(),
            reloj=self.reloj,
            uow=self.uow,
            max_intentos=5,
            bloqueo_minutos=15,
            dias_refresh=30,
        )


@pytest.fixture
def entorno() -> Entorno:
    return Entorno()


async def test_login_correcto_devuelve_access_y_refresh_y_guarda_solo_el_hash(entorno):
    par = await entorno.caso.ejecutar(CELULAR_E164, CONTRASENA)

    assert par.access_token == f"access:{entorno.usuario.id}:aprendiz"
    assert par.refresh_token == "refresh-1"
    assert par.expira_en == 900
    assert par.token_type == "bearer"

    sesion = next(iter(entorno.sesiones.por_id.values()))
    assert sesion.token_hash == "h(refresh-1)"
    assert sesion.token_hash != par.refresh_token
    assert sesion.user_id == entorno.usuario.id
    assert sesion.expires_at - AHORA == timedelta(days=30)


async def test_login_correcto_reinicia_intentos_y_registra_ultimo_login(entorno):
    entorno.usuario.failed_attempts = 3

    await entorno.caso.ejecutar(CELULAR_E164, CONTRASENA)

    assert entorno.usuario.failed_attempts == 0
    assert entorno.usuario.last_login_at == AHORA
    assert entorno.eventos.tipos() == ["login_exitoso"]
    assert entorno.uow.confirmaciones == 1


async def test_celular_local_colombiano_se_normaliza_a_e164(entorno):
    par = await entorno.caso.ejecutar("3001234567", CONTRASENA)

    assert par.access_token.startswith("access:")


async def test_contrasena_incorrecta_suma_un_intento_y_responde_401(entorno):
    with pytest.raises(InvalidCredentials) as error:
        await entorno.caso.ejecutar(CELULAR_E164, "otra-clave")

    assert error.value.http_status == 401
    assert error.value.code == "AUTH_CREDENCIALES_INVALIDAS"
    assert entorno.usuario.failed_attempts == 1
    assert entorno.eventos.tipos() == ["login_fallido"]
    assert entorno.sesiones.por_id == {}


async def test_celular_inexistente_responde_exactamente_igual_que_contrasena_mala(entorno):
    with pytest.raises(InvalidCredentials) as contrasena_mala:
        await entorno.caso.ejecutar(CELULAR_E164, "otra-clave")
    with pytest.raises(InvalidCredentials) as celular_inexistente:
        await entorno.caso.ejecutar("+573009999999", CONTRASENA)

    assert celular_inexistente.value.code == contrasena_mala.value.code
    assert celular_inexistente.value.message == contrasena_mala.value.message
    assert celular_inexistente.value.http_status == contrasena_mala.value.http_status


async def test_celular_con_formato_invalido_responde_como_credencial_invalida(entorno):
    with pytest.raises(InvalidCredentials):
        await entorno.caso.ejecutar("123", CONTRASENA)


async def test_quinto_fallo_bloquea_y_el_sexto_intento_responde_423_aun_con_clave_correcta(entorno):
    for _ in range(4):
        with pytest.raises(InvalidCredentials):
            await entorno.caso.ejecutar(CELULAR_E164, "mala")

    # El quinto fallo responde 401; la cuenta queda bloqueada desde este momento.
    with pytest.raises(InvalidCredentials):
        await entorno.caso.ejecutar(CELULAR_E164, "mala")
    assert entorno.usuario.failed_attempts == 5
    assert "bloqueo" in entorno.eventos.tipos()

    with pytest.raises(UserBlocked) as error:
        await entorno.caso.ejecutar(CELULAR_E164, CONTRASENA)

    assert error.value.http_status == 423
    assert error.value.code == "AUTH_CUENTA_BLOQUEADA"


async def test_cuenta_se_desbloquea_al_pasar_quince_minutos(entorno):
    for _ in range(5):
        with pytest.raises(InvalidCredentials):
            await entorno.caso.ejecutar(CELULAR_E164, "mala")

    entorno.reloj.avanzar(minutes=15, seconds=1)
    par = await entorno.caso.ejecutar(CELULAR_E164, CONTRASENA)

    assert par.access_token.startswith("access:")
    assert entorno.usuario.failed_attempts == 0
    assert entorno.usuario.locked_until is None
    assert "desbloqueo" in entorno.eventos.tipos()


async def test_bloqueo_no_vence_antes_de_quince_minutos(entorno):
    for _ in range(5):
        with pytest.raises(InvalidCredentials):
            await entorno.caso.ejecutar(CELULAR_E164, "mala")

    entorno.reloj.avanzar(minutes=14, seconds=59)

    with pytest.raises(UserBlocked):
        await entorno.caso.ejecutar(CELULAR_E164, CONTRASENA)


async def test_tras_desbloqueo_un_fallo_no_vuelve_a_bloquear_de_inmediato(entorno):
    for _ in range(5):
        with pytest.raises(InvalidCredentials):
            await entorno.caso.ejecutar(CELULAR_E164, "mala")
    entorno.reloj.avanzar(minutes=16)

    with pytest.raises(InvalidCredentials):
        await entorno.caso.ejecutar(CELULAR_E164, "mala")

    assert entorno.usuario.failed_attempts == 1
    assert entorno.usuario.locked_until is None


async def test_usuario_eliminado_no_puede_entrar_con_error_generico(entorno):
    entorno.usuario.status = UserStatus.INACTIVE

    with pytest.raises(InvalidCredentials) as error:
        await entorno.caso.ejecutar(CELULAR_E164, CONTRASENA)

    assert error.value.code == "AUTH_CREDENCIALES_INVALIDAS"
    assert entorno.sesiones.por_id == {}


async def test_hash_con_parametros_viejos_se_recalcula_al_iniciar_sesion():
    entorno = Entorno(necesita_rehash=True)

    await entorno.caso.ejecutar(CELULAR_E164, CONTRASENA)

    assert entorno.usuario.password_hash == entorno.hasher.generate_hash(CONTRASENA)
