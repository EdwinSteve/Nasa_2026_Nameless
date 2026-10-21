# Se construye desde la raíz del repositorio (ver docker-compose.yml): el diagnóstico
# usa el paquete datos_tierra, que vive en ml/.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY ml/pyproject.toml /ml/pyproject.toml
COPY ml/datos_tierra /ml/datos_tierra
COPY ml/surco_ml /ml/surco_ml
COPY backend/pyproject.toml ./
# Editable: surco_ml ubica la raíz del repo por la ruta de sus archivos (/ml/surco_ml -> /)
RUN pip install --upgrade pip && pip install ".[dev]" -e "/ml[gee,modelo]"

# surco_ml busca el catálogo y los modelos relativos a la raíz del repo (aquí, /):
# /data/catalogo_cultivos_mongodb/datos y /ml/modelos_exportados. Los modelo_a_*.ubj no se
# versionan: se copian a ml/modelos_exportados/<corrida>/ antes de construir la imagen.
COPY data/catalogo_cultivos_mongodb/datos /data/catalogo_cultivos_mongodb/datos
COPY ml/modelos_exportados /ml/modelos_exportados
# El oráculo usa las fórmulas FAO-56 del motor agronómico (surco_ml/suelo_motor.py)
COPY scripts/data/agronomic_engine /scripts/data/agronomic_engine

COPY backend/ .

EXPOSE 8000
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
