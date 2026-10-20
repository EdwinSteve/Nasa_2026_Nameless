import re

from app.modules.identidad.infrastructure.security.refresh_tokens import GeneradorRefreshToken


def test_refresh_token_tiene_entropia_suficiente_y_formato_url_seguro():
    token = GeneradorRefreshToken().generar()

    # 32 bytes en base64url sin relleno producen 43 caracteres.
    assert len(token) == 43
    assert re.fullmatch(r"[A-Za-z0-9_-]+", token)


def test_cada_refresh_token_es_distinto():
    generador = GeneradorRefreshToken()

    tokens = {generador.generar() for _ in range(1000)}

    assert len(tokens) == 1000


def test_hash_es_sha256_hexadecimal_de_64_caracteres():
    hash_ = GeneradorRefreshToken().hashear("token-de-prueba")

    assert len(hash_) == 64
    assert re.fullmatch(r"[0-9a-f]{64}", hash_)


def test_hash_es_determinista_y_no_es_el_token():
    generador = GeneradorRefreshToken()

    assert generador.hashear("abc") == generador.hashear("abc")
    assert generador.hashear("abc") != "abc"
    assert generador.hashear("abc") != generador.hashear("abd")


def test_hash_coincide_con_sha256_conocido():
    # SHA-256("abc") es un vector de prueba estándar (FIPS 180-2).
    assert GeneradorRefreshToken().hashear("abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )
