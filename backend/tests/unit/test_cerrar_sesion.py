import pytest

from app.modules.identidad.domain.entity import Role, User, UserStatus
from app.modules.identidad.domain.errors import RefreshTokenInvalid
from app.modules.identidad.domain.values import Email, Phone
from tests.unit.entorno import CONTRASENA, EntornoIdentidad


@pytest.fixture
def entorno() -> EntornoIdentidad:
    return EntornoIdentidad()


def _sesiones_de(entorno, usuario_id):
    return [s for s in entorno.sesiones.por_id.values() if s.user_id == usuario_id]


async def test_logout_revoca_solo_esa_sesion_y_registra_el_evento(entorno):
    primera = await entorno.login()
    segunda = await entorno.login()

    await entorno.cerrar.una(entorno.usuario.id, primera.refresh_token)

    revocadas = [s for s in _sesiones_de(entorno, entorno.usuario.id) if s.revocada]
    assert len(revocadas) == 1
    assert ("logout", entorno.usuario.id, {"alcance": "una"}) in entorno.eventos.registros
    # La otra sesión del mismo usuario (otro dispositivo) sigue viva.
    assert (await entorno.refrescar.ejecutar(segunda.refresh_token)).refresh_token


async def test_refresh_despues_de_logout_responde_401(entorno):
    par = await entorno.login()
    await entorno.cerrar.una(entorno.usuario.id, par.refresh_token)

    with pytest.raises(RefreshTokenInvalid):
        await entorno.refrescar.ejecutar(par.refresh_token)


async def test_logout_es_idempotente_y_no_repite_el_evento(entorno):
    par = await entorno.login()

    await entorno.cerrar.una(entorno.usuario.id, par.refresh_token)
    await entorno.cerrar.una(entorno.usuario.id, par.refresh_token)

    eventos_logout = [e for e in entorno.eventos.tipos() if e == "logout"]
    assert len(eventos_logout) == 1


async def test_logout_de_token_de_otro_usuario_no_revoca_y_no_falla(entorno):
    otro = User(
        phone=Phone("+573002222222"),
        email=Email("otro@finca.co"),
        password_hash=entorno.hasher.generate_hash(CONTRASENA),
        role=Role.APRENDIZ,
        status=UserStatus.ACTIVE,
    )
    entorno.usuarios.agregar(otro)
    token_ajeno = await entorno.iniciar.ejecutar("+573002222222", CONTRASENA)

    await entorno.cerrar.una(entorno.usuario.id, token_ajeno.refresh_token)

    assert not any(s.revocada for s in _sesiones_de(entorno, otro.id))
    assert "logout" not in entorno.eventos.tipos()


async def test_logout_con_token_inexistente_no_falla(entorno):
    await entorno.cerrar.una(entorno.usuario.id, "token-que-nunca-existio")

    assert entorno.uow.confirmaciones == 0


async def test_logout_todas_revoca_todas_las_sesiones_del_usuario(entorno):
    await entorno.login()
    await entorno.login()

    await entorno.cerrar.todas(entorno.usuario.id)

    sesiones = _sesiones_de(entorno, entorno.usuario.id)
    assert len(sesiones) == 2
    assert all(s.revocada for s in sesiones)
    assert ("logout", entorno.usuario.id, {"alcance": "todas"}) in entorno.eventos.registros


async def test_logout_todas_no_toca_sesiones_de_otros_usuarios(entorno):
    otro = User(
        phone=Phone("+573002222222"),
        email=Email("otro@finca.co"),
        password_hash=entorno.hasher.generate_hash(CONTRASENA),
        status=UserStatus.ACTIVE,
    )
    entorno.usuarios.agregar(otro)
    await entorno.login()
    await entorno.iniciar.ejecutar("+573002222222", CONTRASENA)

    await entorno.cerrar.todas(entorno.usuario.id)

    assert all(s.revocada for s in _sesiones_de(entorno, entorno.usuario.id))
    assert not any(s.revocada for s in _sesiones_de(entorno, otro.id))
