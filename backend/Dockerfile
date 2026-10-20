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
COPY backend/pyproject.toml ./
RUN pip install --upgrade pip && pip install ".[dev]" "/ml[gee]"

COPY backend/ .

EXPOSE 8000
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
