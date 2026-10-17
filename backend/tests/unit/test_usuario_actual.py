from uuid import uuid4

import jwt
import pytest

from app.core.config import get_settings
from app.core.errors import ErrorDominio
from app.modules.identidad.api.dependencies import usuario_actual
from app.modules.identidad.domain.entity import Role, User, UserStatus
from app.modules.identidad.domain.values import Email, Phone
from app.modules.identidad.infrastructure.security.jwt_issuer import JwtTokenIssuer
from tests.unit.fakes import UsuariosFalsos


@pytest.fixture
def usuarios() -> UsuariosFalsos:
    repo = UsuariosFalsos()
    repo.agregar(
        User(
            phone=Phone("+573001234567"),
            email=Email("ana@finca.co"),
            password_hash="x",
            role=Role.APRENDIZ,
            status=UserStatus.ACTIVE,
        )
    )
    return repo


def _usuario(usuarios: UsuariosFalsos) -> User:
    return next(iter(usuarios.por_id.values()))


async def _codigo_de_error(corutina) -> str:
    with pytest.raises(ErrorDominio) as error:
        await corutina
    assert error.value.http_status == 401
    return error.value.code


async def test_devuelve_el_usuario_con_access_token_valido(usuarios):
    usuario = _usuario(usuarios)
    token = JwtTokenIssuer().issue_access_token(usuario.id, "aprendiz")

    encontrado = await usuario_actual(authorization=f"Bearer {token}", repo=usuarios)

    assert encontrado.id == usuario.id


async def test_sin_encabezado_responde_401_no_autenticado(usuarios):
    assert await _codigo_de_error(usuario_actual(authorization=None, repo=usuarios)) == "AUTH_NO_AUTENTICADO"


async def test_esquema_distinto_de_bearer_responde_401_no_autenticado(usuarios):
    assert await _codigo_de_error(
        usuario_actual(authorization="Basic abc123", repo=usuarios)
    ) == "AUTH_NO_AUTENTICADO"


async def test_token_mal_formado_responde_401_token_invalido(usuarios):
    assert await _codigo_de_error(
        usuario_actual(authorization="Bearer no.es.un-jwt", repo=usuarios)
    ) == "AUTH_TOKEN_INVALIDO"


async def test_sub_que_no_es_uuid_responde_401_token_invalido(usuarios):
    token = JwtTokenIssuer().issue_access_token(uuid4(), "aprendiz")
    # Se reemplaza el sub por algo que no es UUID, firmando con el mismo secreto.
    claims = JwtTokenIssuer().decode_access_token(token)
    claims["sub"] = "no-es-uuid"
    manipulado = jwt.encode(claims, get_settings().jwt_secreto.get_secret_value(), algorithm="HS256")

    assert await _codigo_de_error(
        usuario_actual(authorization=f"Bearer {manipulado}", repo=usuarios)
    ) == "AUTH_TOKEN_INVALIDO"


async def test_usuario_que_no_existe_responde_401(usuarios):
    token = JwtTokenIssuer().issue_access_token(uuid4(), "aprendiz")

    assert await _codigo_de_error(
        usuario_actual(authorization=f"Bearer {token}", repo=usuarios)
    ) == "AUTH_USUARIO_NO_ENCONTRADO"


async def test_usuario_eliminado_responde_401(usuarios):
    usuario = _usuario(usuarios)
    usuario.status = UserStatus.INACTIVE
    token = JwtTokenIssuer().issue_access_token(usuario.id, "aprendiz")

    assert await _codigo_de_error(
        usuario_actual(authorization=f"Bearer {token}", repo=usuarios)
    ) == "AUTH_USUARIO_NO_ENCONTRADO"
