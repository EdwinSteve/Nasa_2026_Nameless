"""Pruebas de integración contra PostgreSQL real.

Requieren TEST_DATABASE_URL apuntando a una base que termine en `_test`. Sin esa variable,
las pruebas se omiten. Cada prueba vacía las tablas de identidad, así que nunca se debe
apuntar a una base con datos reales.
"""

import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.db import get_session
from app.modules.identidad.infrastructure.security.hasher_argon2 import Argon2Hasher

BACKEND = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def url_pruebas() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Define TEST_DATABASE_URL para ejecutar las pruebas de integración.")
    nombre = make_url(url).database or ""
    if not nombre.endswith("_test"):
        raise RuntimeError(
            f"TEST_DATABASE_URL debe apuntar a una base que termine en '_test' (recibido: {nombre!r})."
        )
    return url


@pytest.fixture(scope="session", autouse=True)
def migraciones(url_pruebas):
    """Aplica el esquema con alembic en un proceso aparte, para que use la URL de pruebas."""
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND,
        env={**os.environ, "DATABASE_URL": url_pruebas},
        check=True,
    )


@pytest.fixture
async def sesion_maker(url_pruebas):
    engine = create_async_engine(url_pruebas, poolclass=NullPool)
    async with engine.begin() as conexion:
        await conexion.execute(
            text(
                "TRUNCATE identidad.eventos_auth, identidad.consentimientos, "
                "identidad.sesiones, identidad.usuarios CASCADE"
            )
        )
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
def app_db(sesion_maker):
    """La app con su dependencia de sesión apuntando a la base de pruebas."""
    from app.api import app

    async def _sesion_de_pruebas():
        async with sesion_maker() as sesion:
            yield sesion

    app.dependency_overrides[get_session] = _sesion_de_pruebas
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def usuario_db(sesion_maker):
    """Crea un usuario activo con contraseña 'MiFinca2026' y celular +573001234567."""
    usuario_id = uuid4()
    async with sesion_maker() as sesion:
        await sesion.execute(
            text(
                "INSERT INTO identidad.usuarios (id, phone, email, password_hash, role, status) "
                "VALUES (:id, :phone, :email, :hash, 'aprendiz', 'activo')"
            ),
            {
                "id": usuario_id,
                "phone": "+573001234567",
                "email": "ana@finca.co",
                "hash": Argon2Hasher().generate_hash("MiFinca2026"),
            },
        )
        await sesion.commit()
    return usuario_id
