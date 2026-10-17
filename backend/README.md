# Backend (FastAPI)

Pendiente: Fase 2 del [roadmap](../docs/02-roadmap.md).

Estructura prevista:
```
backend/
  app/
    main.py          # FastAPI
    datos/           # adaptadores: power.py, smap.py, soilgrids.py ...
    motor/           # filtros, puntajes, rotación
    rag/             # asistente
  tests/
```

## Módulo identidad

Login, renovación de sesión y cierre de sesión (issues ID-04, ID-05, ID-06).

| Método | Ruta | Auth | Respuesta |
|---|---|---|---|
| POST | `/api/v1/auth/login` | pública | 200 tokens · 401 credenciales · 423 cuenta bloqueada |
| POST | `/api/v1/auth/refresh` | refresh token | 200 tokens nuevos · 401 sesión inválida |
| POST | `/api/v1/auth/logout` | Bearer + refresh token | 204 |
| POST | `/api/v1/auth/logout-todo` | Bearer | 204 |

La documentación interactiva está en `/docs`.

### Pruebas

```bash
pip install -e ".[dev]"

# Pruebas unitarias y de API (no necesitan base de datos)
pytest

# Pruebas de integración contra PostgreSQL. Usa una base dedicada que termine en _test.
# Cada prueba vacía las tablas de identidad, así que NUNCA apuntar a una base con datos reales.
createdb surco_test
TEST_DATABASE_URL=postgresql+asyncpg://surco:surco@localhost:5432/surco_test pytest tests/integration
```

Sin `TEST_DATABASE_URL`, las pruebas de integración se omiten.

### Migraciones

```bash
DATABASE_URL=postgresql+asyncpg://surco:surco@localhost:5432/surco alembic upgrade head
```
