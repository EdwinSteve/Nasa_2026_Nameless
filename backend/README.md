# Backend SURCO (FastAPI)

API REST de SURCO. Es un monolito modular: cada módulo tiene su propio esquema de PostgreSQL y sus capas `domain` (entidades, errores y puertos), `application` (casos de uso), `infrastructure` (adaptadores) y `api` (rutas y schemas).

| Módulo | Qué hace | Esquema |
|---|---|---|
| `identidad` | Registro, login, refresh y logout con JWT; política de privacidad | `identidad` |
| `territorio` | Municipios y centros poblados del Huila (DIVIPOLA del DANE) | (JSON en memoria) |
| `fincas` | Fincas, lotes (polígono y área) y preferencias del productor | `fincas` |
| `diagnostico` | Diagnóstico satelital del lote: clima, humedad, suelo y verdor | `diagnostico` |
| `recomendacion` | Cultivos recomendados por el modelo predictivo (`surco_ml`, modelo A) | `recomendacion` |

La documentación interactiva queda en `http://localhost:8000/docs`.

## Endpoints (`/api/v1`)

| Método | Ruta | Auth | Qué hace |
|---|---|---|---|
| GET | `/politicas/vigente` | pública | Versión, texto y ruta de la política que se acepta al registrarse |
| POST | `/auth/registro` | pública | Crea el productor y deja la sesión iniciada (201) |
| POST | `/auth/login` | pública | 200 tokens · 401 credenciales · 423 cuenta bloqueada |
| POST | `/auth/refresh` | refresh token | Tokens nuevos; el refresh anterior deja de servir |
| POST | `/auth/logout` y `/auth/logout-todo` | Bearer | Cierra una sesión o todas (204) |
| GET | `/territorio/municipios?departamento=41` | pública | Los 37 municipios del Huila |
| GET | `/territorio/municipios/{codigo}/corregimientos` | pública | Casco urbano y centros poblados del municipio |
| GET | `/territorio/elevacion?lat=&lon=` | pública | Altitud NASA SRTM y municipio más cercano (chip de la bienvenida) |
| POST | `/fincas` | Bearer | Crea una finca (valida municipio y centro poblado) |
| POST | `/fincas/{finca_id}/lotes` | Bearer | Crea un lote: valida el polígono, calcula el área y guarda su punto medio (`centroide`) |
| GET | `/lotes/{lote_id}` | Bearer | Detalle del lote con nombres de municipio y corregimiento |
| PUT | `/usuarios/me/preferencias` | Bearer | Orden de las cuatro prioridades del productor (204) |
| POST | `/lotes/{lote_id}/diagnostico` | Bearer | Inicia el diagnóstico en segundo plano (202 + `tarea_id`) |
| GET | `/lotes/{lote_id}/diagnostico/{tarea_id}` | Bearer | Avance del diagnóstico (la UI lo consulta cada 2 s) |
| GET | `/recomendaciones/modelo` | pública | Si el servidor tiene el modelo predictivo y, si no, qué archivos faltan |
| POST | `/lotes/{lote_id}/recomendaciones` | Bearer | Pide la recomendación de cultivos (202); `fecha_siembra` opcional, día 1 o 16 |
| GET | `/lotes/{lote_id}/recomendaciones/{id}` | Bearer | Los 10 mejores cultivos, los descartados y el contexto del lote |

Los errores siempre llegan como `{ "code", "message", "details"? }`. Un recurso de otro productor responde 404, igual que uno inexistente.

### Diagnóstico

Los cuatro pasos corren en paralelo con el servicio [`datos_tierra`](../ml/datos_tierra/README.md) y cada uno guarda su resultado al terminar:

| Paso | Fuente | Qué resume | Tiempo medido |
|---|---|---|---|
| Clima | NASA POWER 1981–hoy + SRTM | Lluvia anual y temperatura media, corregida por elevación (ADR 0002) | ~5 s |
| Humedad | NASA SMAP L4 (Earth Engine) | Humedad de la zona de raíces de los últimos 30 días | ~6 s |
| Suelo | SoilGrids 0–30 cm por Earth Engine (API de ISRIC de respaldo) | Textura USDA, pH y materia orgánica | ~2 s (API: 10–60 s) |
| Verdor | NASA MODIS NDVI (Earth Engine) | NDVI de la última imagen sin nubes | ~4 s |

Un paso que falla (por ejemplo, sin `GEE_PROJECT`) queda como fallido y los demás siguen. El diagnóstico termina "lista" si al menos un paso salió bien.

### Recomendación de cultivos

Usa `surco_ml.predecir` (el mismo código del entrenamiento) en el punto medio del lote: baja 45 años de clima, calcula las 131 features del día de la siembra, predice con el modelo A y aplica la calibración y los filtros duros del catálogo (altitud y pH). Tarda unos 25–40 s y corre en segundo plano.

**Los modelos no están en el repositorio** (los `.ubj` pesan hasta 150 MB). Para activarla, copia desde la máquina de entrenamiento:

```
ml/modelos_exportados/tiempo/modelo_a_puntaje.ubj
ml/modelos_exportados/tiempo/modelo_a_exito.ubj
ml/modelos_exportados/tiempo/modelo_a_riego_mm.ubj
ml/modelos_exportados/tiempo/modelo_a_dias_estres.ubj
```

`informe.json` y `calibracion.json` sí se versionan. Otra corrida se elige con `MODELO_CORRIDA`. Sin los `.ubj`, `GET /recomendaciones/modelo` dice cuáles faltan y la UI muestra un aviso en lugar del botón.

## Cómo correrlo

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pip install -e "../ml[gee,modelo]"   # datos_tierra (diagnóstico) y surco_ml (recomendación)

cp .env.example .env                 # y poner un JWT_SECRETO de 64+ caracteres
                                     # (python -c "import secrets; print(secrets.token_hex(48))")

# Base de datos: PostgreSQL 16 (con Docker, o con podman cambiando el comando)
docker run -d --name surco-pg -e POSTGRES_USER=surco -e POSTGRES_PASSWORD=surco \
  -e POSTGRES_DB=surco -p 5432:5432 postgres:16-alpine

alembic upgrade head
uvicorn app.api:app --reload --port 8000
```

Para la humedad y el verdor del diagnóstico: `GEE_PROJECT=<id>` en `.env` y autenticar Earth Engine una vez con `python -c "import ee; ee.Authenticate()"`.

Con Docker Compose (API + PostgreSQL; la imagen se construye desde la raíz del repo para incluir `ml/`):

```bash
cd backend
JWT_SECRETO=$(python -c "import secrets; print(secrets.token_hex(48))") GEE_PROJECT=<id> docker compose up --build
```

## Pruebas

```bash
pytest                               # unitarias y de API: no necesitan base de datos

# Integración contra PostgreSQL. Usa una base dedicada que termine en _test:
# cada prueba vacía las tablas, así que NUNCA apuntar a una base con datos reales.
createdb surco_test
TEST_DATABASE_URL=postgresql+asyncpg://surco:surco@localhost:5432/surco_test pytest tests/integration
```

Sin `TEST_DATABASE_URL`, las pruebas de integración se omiten.

## Migraciones

| Revisión | Contenido |
|---|---|
| 0001–0003 | Esquema `identidad`: usuarios, política, consentimientos, sesiones, eventos y registro de productor |
| 0004 | Esquema `fincas`: fincas, lotes y preferencias del productor |
| 0005 | Esquema `diagnostico`: tareas y pasos |
| 0006 | Esquema `recomendacion`: recomendaciones de cultivos y su resultado |

## Datos de territorio

`app/modules/territorio/infrastructure/datos/divipola.json` sale de los datos abiertos del DANE (datos.gov.co, conjuntos `gdxc-w37w` y `xaxy-8nri`). Para regenerarlo o agregar departamentos: `python scripts/actualizar_divipola.py 41 73`.
