#!/usr/bin/env bash
# Configura Google Earth Engine para datos_tierra. Lo único manual es aceptar en el navegador.
#
#   bash ml/autenticar_gee.sh            (desde cualquier carpeta)
set -euo pipefail

ML="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAIZ="$(dirname "$ML")"
ENV="$RAIZ/.env"
PY="$ML/.venv/bin/python"

if [[ ! -x "$PY" ]]; then
  echo "Creando el entorno ml/.venv..."
  python3 -m venv "$ML/.venv"
  "$ML/.venv/bin/pip" install -q -r "$ML/requirements.txt"
fi

[[ -f "$ENV" ]] || cp "$RAIZ/.env.example" "$ENV"
PROYECTO="$(grep -E '^GEE_PROJECT=' "$ENV" | cut -d= -f2- | tr -d '"'\'' ' || true)"
if [[ -z "$PROYECTO" ]]; then
  echo "Escribe el Project ID de Google Cloud registrado en Earth Engine"
  echo "(el ID, no el nombre; lo ves en https://console.cloud.google.com)."
  read -r -p "Project ID: " PROYECTO
  PROYECTO="$(echo "$PROYECTO" | tr -d '"'\'' ')"
  [[ -n "$PROYECTO" ]] || { echo "El Project ID no puede quedar vacío."; exit 1; }
  if grep -qE '^GEE_PROJECT=' "$ENV"; then
    sed -i "s|^GEE_PROJECT=.*|GEE_PROJECT=$PROYECTO|" "$ENV"
  else
    echo "GEE_PROJECT=$PROYECTO" >> "$ENV"
  fi
  echo "Guardado en .env"
fi

echo ""
echo "Se va a abrir el navegador: elige tu cuenta de Google y acepta los permisos."
"$PY" -c "import ee; ee.Authenticate()"

echo ""
echo "Probando la conexión con el proyecto $PROYECTO..."
"$PY" -c "
import ee
ee.Initialize(project='$PROYECTO')
assert ee.Number(1).add(1).getInfo() == 2
print('Earth Engine listo.')
"

echo ""
echo "Prueba de SMAP, IMERG y MODIS en Villavieja (enero de 2024)..."
cd "$ML"
GEE_PROJECT="$PROYECTO" "$PY" -m datos_tierra lote --lat 3.22 --lon -75.22 \
  --inicio 2024-01-01 --fin 2024-01-31 --fuentes power,dem,smap,imerg,modis \
  --out "$RAIZ/data/processed/prueba_gee_villavieja.json"
