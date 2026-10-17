from datetime import timedelta

import pytest

from app.modules.identidad.domain.entity import UserStatus
from app.modules.identidad.domain.errors import RefreshTokenInvalid
from tests.unit.entorno import AHORA, EntornoIdentidad


@pytest.fixture
def entorno() -> EntornoIdentidad:
    return EntornoIdentidad()


async def test_rotacion_devuelve_tokens_nuevos_y_marca_el_anterior_como_usado(entorno):
    inicio = await entorno.login()

    nuevo = await entorno.refrescar.ejecutar(inicio.refresh_token)

    assert nuevo.refresh_token != inicio.refresh_token
    assert nuevo.access_token == f"access:{entorno.usuario.id}:aprendiz"
    assert nuevo.expira_en == 900

    anterior = entorno.sesiones.por_id[
        next(sid for sid, s in entorno.sesiones.por_id.items()
             if s.token_hash == f"h({inicio.refresh_token})")
    ]
    nueva = entorno.sesiones.por_id[
        next(sid for sid, s in entorno.sesiones.por_id.items()
             if s.token_hash == f"h({nuevo.refresh_token})")
    ]
    assert anterior.used_at == AHORA
    assert anterior.replaced_by == nueva.id
    assert nueva.used_at is None
    assert nueva.family_id == anterior.family_id


async def test_reutilizar_un_token_usado_revoca_toda_la_familia(entorno):
    inicio = await entorno.login()
    nuevo = await entorno.refrescar.ejecutar(inicio.refresh_token)

    with pytest.raises(RefreshTokenInvalid) as error:
        await entorno.refrescar.ejecutar(inicio.refresh_token)

    assert error.value.http_status == 401
    assert error.value.code == "AUTH_REFRESH_INVALIDO"
    assert all(s.revocada for s in entorno.sesiones.por_id.values())
    assert ("refresh", entorno.usuario.id, {"motivo": "reutilizado"}) in entorno.eventos.registros

    # El token nuevo de esa familia también queda muerto.
    with pytest.raises(RefreshTokenInvalid):
        await entorno.refrescar.ejecutar(nuevo.refresh_token)


async def test_cadena_de_rotaciones_conserva_la_familia_y_solo_el_ultimo_sigue_vigente(entorno):
    par = await entorno.login()
    for _ in range(3):
        par = await entorno.refrescar.ejecutar(par.refresh_token)

    familias = {s.family_id for s in entorno.sesiones.por_id.values()}
    vigentes = [s for s in entorno.sesiones.por_id.values() if not s.usada and not s.revocada]
    assert len(familias) == 1
    assert len(entorno.sesiones.por_id) == 4
    assert len(vigentes) == 1


async def test_token_expirado_responde_401(entorno):
    inicio = await entorno.login()
    entorno.reloj.avanzar(days=30, seconds=1)

    with pytest.raises(RefreshTokenInvalid):
        await entorno.refrescar.ejecutar(inicio.refresh_token)


async def test_token_inventado_responde_401(entorno):
    with pytest.raises(RefreshTokenInvalid):
        await entorno.refrescar.ejecutar("token-que-nunca-existio")


async def test_usuario_bloqueado_temporalmente_no_puede_refrescar(entorno):
    inicio = await entorno.login()
    entorno.usuario.locked_until = AHORA + timedelta(minutes=15)

    with pytest.raises(RefreshTokenInvalid):
        await entorno.refrescar.ejecutar(inicio.refresh_token)


async def test_usuario_eliminado_no_puede_refrescar(entorno):
    inicio = await entorno.login()
    entorno.usuario.status = UserStatus.INACTIVE

    with pytest.raises(RefreshTokenInvalid):
        await entorno.refrescar.ejecutar(inicio.refresh_token)


async def test_refresh_confirma_la_transaccion(entorno):
    inicio = await entorno.login()
    confirmaciones_antes = entorno.uow.confirmaciones

    await entorno.refrescar.ejecutar(inicio.refresh_token)

    assert entorno.uow.confirmaciones == confirmaciones_antes + 1
