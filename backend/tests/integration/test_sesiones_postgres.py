import asyncio

import httpx
import pytest
from sqlalchemy import text

from app.modules.identidad.infrastructure.security.refresh_tokens import GeneradorRefreshToken

LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"
LOGOUT_TODO = "/api/v1/auth/logout-todo"
CELULAR = "+573001234567"
CONTRASENA = "MiFinca2026"

hash_de = GeneradorRefreshToken().hashear


@pytest.fixture
async def cliente(app_db):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app_db), base_url="http://test") as c:
        yield c


async def login(cliente, celular=CELULAR, contrasena=CONTRASENA) -> dict:
    respuesta = await cliente.post(LOGIN, json={"celular": celular, "contrasena": contrasena})
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


async def filas_sesiones(sesion_maker) -> list[dict]:
    async with sesion_maker() as sesion:
        resultado = await sesion.execute(
            text(
                "SELECT id, refresh_token_hash, family_id, used_at, replaced_by, revoked_at "
                "FROM identidad.sesiones"
            )
        )
        return [dict(fila) for fila in resultado.mappings()]


async def eventos(sesion_maker) -> list[str]:
    async with sesion_maker() as sesion:
        resultado = await sesion.execute(text("SELECT event FROM identidad.eventos_auth ORDER BY created_at"))
        return [fila[0] for fila in resultado]


async def test_login_guarda_solo_el_hash_y_registra_el_ultimo_login(usuario_db, sesion_maker, cliente):
    par = await login(cliente)

    filas = await filas_sesiones(sesion_maker)
    assert len(filas) == 1
    assert filas[0]["refresh_token_hash"] == hash_de(par["refresh_token"])
    assert par["refresh_token"] not in str(filas)
    assert await eventos(sesion_maker) == ["login_exitoso"]

    async with sesion_maker() as sesion:
        ultimo = (await sesion.execute(text("SELECT last_login_at FROM identidad.usuarios"))).scalar_one()
    assert ultimo is not None


async def test_rotacion_enlaza_los_tokens_y_reutilizar_revoca_la_familia(usuario_db, sesion_maker, cliente):
    inicio = await login(cliente)
    nuevo = (await cliente.post(REFRESH, json={"refresh_token": inicio["refresh_token"]})).json()

    filas = await filas_sesiones(sesion_maker)
    anterior = next(f for f in filas if f["refresh_token_hash"] == hash_de(inicio["refresh_token"]))
    actual = next(f for f in filas if f["refresh_token_hash"] == hash_de(nuevo["refresh_token"]))
    assert anterior["used_at"] is not None
    assert anterior["replaced_by"] == actual["id"]
    assert actual["used_at"] is None
    assert actual["family_id"] == anterior["family_id"]

    reuso = await cliente.post(REFRESH, json={"refresh_token": inicio["refresh_token"]})

    assert reuso.status_code == 401
    assert reuso.json()["code"] == "AUTH_REFRESH_INVALIDO"
    assert all(f["revoked_at"] is not None for f in await filas_sesiones(sesion_maker))
    assert (await cliente.post(REFRESH, json={"refresh_token": nuevo["refresh_token"]})).status_code == 401
    assert "refresh" in await eventos(sesion_maker)


async def test_refresh_concurrente_con_el_mismo_token_solo_tiene_un_ganador(usuario_db, sesion_maker, cliente):
    """FOR UPDATE: cinco peticiones simultáneas con el mismo token. Solo una gana."""
    inicio = await login(cliente)
    cuerpo = {"refresh_token": inicio["refresh_token"]}

    respuestas = await asyncio.gather(*(cliente.post(REFRESH, json=cuerpo) for _ in range(5)))

    codigos = sorted(r.status_code for r in respuestas)
    assert codigos.count(200) == 1, codigos
    assert codigos.count(401) == 4, codigos


async def test_logout_revoca_una_sesion_y_logout_todo_revoca_el_resto(usuario_db, sesion_maker, cliente):
    primera = await login(cliente)
    segunda = await login(cliente)

    cierre = await cliente.post(
        LOGOUT,
        json={"refresh_token": primera["refresh_token"]},
        headers={"Authorization": f"Bearer {primera['access_token']}"},
    )
    assert cierre.status_code == 204

    filas = await filas_sesiones(sesion_maker)
    revocadas = [f for f in filas if f["revoked_at"] is not None]
    assert [f["refresh_token_hash"] for f in revocadas] == [hash_de(primera["refresh_token"])]
    assert (await cliente.post(REFRESH, json={"refresh_token": segunda["refresh_token"]})).status_code == 200

    todo = await cliente.post(LOGOUT_TODO, headers={"Authorization": f"Bearer {segunda['access_token']}"})
    assert todo.status_code == 204
    assert all(f["revoked_at"] is not None for f in await filas_sesiones(sesion_maker))
    assert "logout" in await eventos(sesion_maker)


async def test_bloqueo_se_guarda_en_la_base_y_bloquea_la_clave_correcta(usuario_db, sesion_maker, cliente):
    for _ in range(5):
        await cliente.post(LOGIN, json={"celular": CELULAR, "contrasena": "mala"})

    async with sesion_maker() as sesion:
        intentos, bloqueada_hasta = (await sesion.execute(
            text("SELECT failed_attempts, locked_until FROM identidad.usuarios")
        )).one()
    assert intentos == 5
    assert bloqueada_hasta is not None

    respuesta = await cliente.post(LOGIN, json={"celular": CELULAR, "contrasena": CONTRASENA})

    assert respuesta.status_code == 423
    assert respuesta.json()["code"] == "AUTH_CUENTA_BLOQUEADA"
    assert "bloqueo" in await eventos(sesion_maker)
