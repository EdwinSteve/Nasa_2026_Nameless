# Guía: máquina de entrenamiento (RTX 5060 Ti 16 GB)

> Fecha: 2026-10-17. Paso a paso para dejar la máquina con GPU lista y arrancar el entrenamiento del modelo predictivo de SURCO.
> Arquitectura del modelo: [ml/README.md](README.md). Servicio de datos: [ml/datos_tierra/README.md](datos_tierra/README.md). Por qué estos datos: [estudio de datos](../docs/datos/estudio-datos-modelo.md).

## 1. Dónde estamos

| Etapa (ver [ml/README.md §10](README.md#10-ruta-de-trabajo)) | Estado | Dónde |
|---|---|---|
| Arquitectura del modelo | ✅ Definida | [ml/README.md](README.md) |
| Estudio de datos | ✅ Hecho | [docs/datos/estudio-datos-modelo.md](../docs/datos/estudio-datos-modelo.md) |
| **0. Arreglar los datos** | ✅ Servicio `datos_tierra` con las 7 fuentes probadas en vivo, incluida Earth Engine | [ml/datos_tierra/](datos_tierra/README.md) |
| Catálogo de cultivos | ✅ 44 cultivos y 81 variedades en JSON y scripts de Mongo | [data/catalogo_cultivos_mongodb/](../data/catalogo_cultivos_mongodb/README.md) |
| Motor de riego (fórmulas 4.9 a 4.15) | ✅ Del PR #12 | [scripts/data/agronomic_engine/](../scripts/data/agronomic_engine/README.md) |
| **2a. Puntos y descarga masiva** | ⏳ **Primera tarea en esta máquina** | Sección 4 |
| 1. Oráculo agronómico | ⏳ Siguiente | Sección 6 |
| 2b. Dataset (etiquetas + features) | ⏳ | Sección 6 |
| 3. Modelo A (XGBoost en GPU) | ⏳ | Sección 6 |
| 4 a 6. Calibración, integración, modelo B | ⏳ | [ml/README.md](README.md) |

## 2. Requisitos de la máquina

| Requisito | Detalle |
|---|---|
| Driver NVIDIA | **570 o superior** (Blackwell). Comprobar con `nvidia-smi` |
| Python | **3.12** recomendado. 3.14 todavía no tiene ruedas de todas las librerías (numba, shap) |
| Git | Con acceso al repo `EdwinSteve/Nasa_2026_Nameless` |
| Disco | ~20 GB libres: datos crudos (~3 GB), dataset en Parquet (~10 GB) y modelos |
| Red | Estable durante la descarga masiva (horas) |
| Cuenta Google | La misma con la que se registró el proyecto de Earth Engine |

No hace falta CUDA Toolkit aparte: PyTorch y XGBoost traen sus propias librerías de CUDA. Solo hace falta el driver.

## 3. Instalación paso a paso

### Linux

```bash
# 1. Clonar el repo y entrar a la rama
git clone git@github.com:EdwinSteve/Nasa_2026_Nameless.git
cd Nasa_2026_Nameless
git switch feature/datos-tierra        # o main, cuando se haya fusionado la MR

# 2. Entorno con Python 3.12
cd ml
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# 3. PyTorch con CUDA 12.8 PRIMERO, luego el resto
pip install torch --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements-entrenamiento.txt

# 4. .env con el proyecto de Earth Engine (el mismo de la otra máquina)
cp ../.env.example ../.env             # y escribir GEE_PROJECT=... en ../.env

# 5. Autenticar Earth Engine: solo pide aceptar en el navegador
bash autenticar_gee.sh

# 6. Verificar todo
python verificar_entorno.py
pytest
```

### Windows (PowerShell)

```powershell
# 1. Clonar y rama
git clone git@github.com:EdwinSteve/Nasa_2026_Nameless.git
cd Nasa_2026_Nameless
git switch feature/datos-tierra

# 2. Entorno con Python 3.12 (instalado desde python.org con "py launcher")
cd ml
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1          # si lo bloquea: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
python -m pip install --upgrade pip

# 3. PyTorch con CUDA 12.8 y el resto
pip install torch --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements-entrenamiento.txt

# 4. .env (editarlo y escribir GEE_PROJECT=...)
Copy-Item ..\.env.example ..\.env
notepad ..\.env

# 5. Autenticar Earth Engine (abre el navegador)
python -c "import ee; ee.Authenticate()"

# 6. Verificar
python verificar_entorno.py
pytest
```

### Qué debe mostrar `verificar_entorno.py`

Todo en ✅. La línea clave es la de la GPU, que debe verse más o menos así:

```
✅ GPU con PyTorch   NVIDIA GeForce RTX 5060 Ti, sm_120, 15.9 GB, CUDA 12.8, bf16 ≈ ... TFLOPS
```

Las credenciales de Earth Engine **son por máquina**: hay que autenticar de nuevo aquí aunque ya se haya hecho en la laptop. El `GEE_PROJECT` sí es el mismo.

## 4. Primera tarea: puntos y descarga masiva

Todo se ejecuta desde `ml/` con el entorno activado. El `.env` se carga solo.

### 4.1 Prueba corta (5 minutos)

Antes de lanzar 600 puntos, medir cuánto tarda uno completo con Earth Engine:

```bash
python -m datos_tierra lote --lat 2.69 --lon -75.33 --inicio 2015-04-01 --fin 2024-12-31 \
  --out ../data/raw/prueba_campoalegre.json.gz
```

Anotar el tiempo de cada fuente. SMAP con 10 años y la serie de IMERG todavía no se han medido.

### 4.2 Elegir los puntos de entrenamiento

```bash
python -m datos_tierra puntos --n 450 --n-huila 150 --out configs/puntos.csv
```

El comando toma puntos al azar sobre píxeles de **cultivo** de MODIS Land Cover (clases IGBP 12 y 14), 150 en el Huila y 450 en el resto de Colombia, con semilla fija (`--semilla 7`). El archivo `configs/puntos.csv` **sí se versiona**, para que cualquiera reproduzca el mismo dataset.

### 4.3 Descarga masiva

```bash
# Linux: dentro de tmux o screen para que no se corte al cerrar la terminal
tmux new -s descarga
python -m datos_tierra masivo --puntos configs/puntos.csv --inicio 1981-01-01 --fin 2025-12-31
# Ctrl+B y luego D para salir sin detenerla; tmux attach -t descarga para volver
```

```powershell
# Windows: desactivar la suspensión mientras corre
powercfg /change standby-timeout-ac 0
python -m datos_tierra masivo --puntos configs/puntos.csv --inicio 1981-01-01 --fin 2025-12-31
```

- Se crea un `data/raw/entrenamiento/<id>.json.gz` por punto. `data/raw/` no se versiona.
- **Se puede reanudar:** si se corta, se vuelve a lanzar el mismo comando y se salta lo que ya existe.
- Cada fuente se recorta sola a su cobertura: POWER desde 1981, IMERG desde 2000, SMAP desde 2015.
- Tiempo esperado: entre 2 y 10 min por punto (SoilGrids es lo más lento), es decir **de 1 a 3 días** para los 600. Se puede empezar a construir el oráculo con los primeros puntos mientras tanto.
- Si un punto falla, el error queda en pantalla y la descarga sigue con el siguiente.

## 5. El catálogo de cultivos en esta máquina

Para entrenar **no hace falta MongoDB**: el oráculo lee directamente `data/catalogo_cultivos_mongodb/datos/cultivos.json`, que es el mismo contenido de `surco_agro`. Si se quiere tener la base local:

```bash
cd data/catalogo_cultivos_mongodb
mongosh "mongodb://localhost:27017" scripts/01_crear_base.js
mongosh "mongodb://localhost:27017" scripts/02_cargar_datos.js
```

## 6. Lo que sigue: oráculo, dataset y modelo A

Detalle completo en [ml/README.md](README.md). Archivos a crear, en este orden:

| # | Archivo | Qué hace | Cómo saber que está bien |
|---|---|---|---|
| 1 | `surco_ml/oraculo/simulador.py` | Para un punto, una fecha de siembra y un cultivo: corta la serie en fases según `duracion_dias`, compara cada fase con sus trapecios y corre el balance hídrico con `derived_et0_mm` × Kc | El maíz en Neiva sale mal en floración sin riego, igual que en `ejemplo_modelo.py` |
| 2 | `surco_ml/oraculo/etiquetas.py` | Corre el simulador para 600 puntos × 44 años × 24 fechas × 44 cultivos con NumPy o Numba y guarda Parquet | ~28 M de filas; tiempo en horas, no en días |
| 3 | `surco_ml/features/construir.py` | Features del día de siembra: ventanas de 30, 90 y 365 días, SMAP, ENSO, suelo, sitio y climatología **dejando el año fuera** (`climatologia_diaria(..., excluir_anio=...)`) | Prueba automática: ninguna feature usa fechas posteriores a la siembra |
| 4 | `surco_ml/modelos/gbdt.py` | XGBoost en GPU con `QuantileDMatrix`, cuantiles p10/p50/p90 y SHAP | Le gana a la línea base de climatología en 2019-2024 |

Usar estas columnas del JSON (ya vienen calculadas por `datos_tierra`):
- Temperatura: `derived_t2m_corr`, `derived_t2m_max_corr` y `derived_t2m_min_corr`. **Nunca `power_t2m*` sin corregir.**
- Lluvia: `derived_precip_mm`.
- ET0: `derived_et0_mm`.
- Suelo a la raíz de cada cultivo: `suelo.promedio_hasta(soil['layers'], propiedad, Zr * 100)`.

## 7. Convenciones

- **Ramas:** una por etapa (`feature/oraculo`, `feature/dataset`, `feature/modelo-a`) y entran por MR a `main`.
- **No se versiona:** `data/raw/`, `.venv/`, `mlruns/` ni los Parquet grandes. Sí se versiona `configs/puntos.csv` y los modelos finales exportados si pesan menos de 50 MB.
- **Reproducibilidad:** semilla fija en todo (`7`) y la versión del catálogo (`version` de cada cultivo) se registra en MLflow con cada experimento.
- **Experimentos:** `mlflow ui` desde `ml/` y se abre http://localhost:5000.

## 8. Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `torch.cuda.is_available()` da `False` o aparece *sm_120 is not compatible* | PyTorch compilado con CUDA 12.4 o anterior | `pip uninstall torch` y reinstalar con `--index-url https://download.pytorch.org/whl/cu128` |
| `nvidia-smi` no existe o el driver es menor a 570 | Driver viejo | Actualizar el driver de NVIDIA |
| `Too many concurrent aggregations` en Earth Engine | Demasiados bloques en paralelo | Bajar `HILOS` en `datos_tierra/fuentes/gee.py` de 4 a 2 |
| `Project ... is not registered to use Earth Engine` | El proyecto no está registrado o es otro ID | Revisar `GEE_PROJECT` en `.env` y el registro en code.earthengine.google.com/register |
| SoilGrids responde 429 o tarda mucho | Límite de ~5 consultas por minuto | Nada: el servicio reintenta solo. El suelo se pide una vez por punto |
| OpenTopoData responde 429 | Límite de 1000 consultas por día | El modo masivo pide 100 puntos por consulta: 600 puntos son 6 consultas |
| `numba` o `shap` no instalan | Python 3.13 o 3.14 | Crear el entorno con Python 3.12 |
