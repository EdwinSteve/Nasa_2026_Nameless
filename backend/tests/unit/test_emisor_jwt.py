from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
import pytest

from app.core.config import get_settings
from app.modules.identidad.infrastructure.security.jwt_issuer import JwtTokenIssuer

USER_ID = UUID("6f1c2d7e-1b2a-4c3d-8e9f-0a1b2c3d4e5f")


@pytest.fixture
def emisor() -> JwtTokenIssuer:
    return JwtTokenIssuer()


def test_access_token_contiene_los_claims_del_contrato(emisor):
    token = emisor.issue_access_token(USER_ID, "aprendiz")

    claims = emisor.decode_access_token(token)

    assert claims["sub"] == str(USER_ID)
    assert claims["rol"] == "aprendiz"
    assert claims["iss"] == "surco-api"
    assert claims["aud"] == "surco-app"
    assert {"iat", "exp", "jti"} <= claims.keys()


def test_access_token_no_contiene_datos_personales(emisor):
    token = emisor.issue_access_token(USER_ID, "admin")

    claims = emisor.decode_access_token(token)

    assert "celular" not in claims
    assert "phone" not in claims
    assert "email" not in claims
    assert "nombre" not in claims


def test_expira_quince_minutos_despues_de_emitirse(emisor):
    token = emisor.issue_access_token(USER_ID, "aprendiz")

    claims = emisor.decode_access_token(token)

    assert claims["exp"] - claims["iat"] == 900
    assert emisor.duracion_segundos == 900


def test_cada_token_tiene_jti_distinto(emisor):
    primero = emisor.decode_access_token(emisor.issue_access_token(USER_ID, "aprendiz"))
    segundo = emisor.decode_access_token(emisor.issue_access_token(USER_ID, "aprendiz"))

    assert primero["jti"] != segundo["jti"]


def test_token_expirado_es_rechazado(emisor):
    ahora = datetime.now(timezone.utc)
    vencido = jwt.encode(
        {
            "sub": str(USER_ID),
            "rol": "aprendiz",
            "iss": "surco-api",
            "aud": "surco-app",
            "iat": int((ahora - timedelta(minutes=20)).timestamp()),
            "exp": int((ahora - timedelta(minutes=5)).timestamp()),
            "jti": str(uuid4()),
        },
        get_settings().jwt_secreto.get_secret_value(),
        algorithm="HS256",
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        emisor.decode_access_token(vencido)


def test_firma_invalida_es_rechazada(emisor):
    token = emisor.issue_access_token(USER_ID, "aprendiz")
    partes = token.split(".")
    partes[2] = partes[2][:-4] + ("AAAA" if not partes[2].endswith("AAAA") else "BBBB")
    manipulado = ".".join(partes)

    with pytest.raises(jwt.InvalidSignatureError):
        emisor.decode_access_token(manipulado)


def test_token_firmado_con_otro_secreto_es_rechazado(emisor):
    ajeno = jwt.encode(
        {"sub": str(USER_ID), "rol": "admin", "iss": "surco-api", "aud": "surco-app",
         "iat": 0, "exp": 9999999999, "jti": "x"},
        "otro-secreto-" + "y" * 64,
        algorithm="HS256",
    )

    with pytest.raises(jwt.InvalidSignatureError):
        emisor.decode_access_token(ajeno)


def test_audiencia_incorrecta_es_rechazada(emisor):
    ajena = jwt.encode(
        {"sub": str(USER_ID), "rol": "admin", "iss": "surco-api", "aud": "otra-app",
         "iat": 0, "exp": 9999999999, "jti": "x"},
        get_settings().jwt_secreto.get_secret_value(),
        algorithm="HS256",
    )

    with pytest.raises(jwt.InvalidAudienceError):
        emisor.decode_access_token(ajena)
