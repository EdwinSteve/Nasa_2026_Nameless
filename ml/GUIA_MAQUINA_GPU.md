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
| Entorno de la máquina (RTX 5060 Ti, `ml/.venv`) | ✅ `verificar_entorno.py` en verde | Sección 3 |
| **2a. Puntos** | ✅ 397 puntos en `configs/puntos.csv` | Sección 4.2 |
| **2a. Descarga masiva** | ⏳ En curso: clima primero, suelo cuando SoilGrids vuelva | Sección 4.3 |
| 1. Oráculo agronómico | ✅ `surco_ml/oraculo/` con pruebas | Sección 6 |
| 2b. Dataset (etiquetas + features) | ✅ Código y prueba de fuga; se arma con los puntos descargados | Sección 6 |
| 3. Modelo A (XGBoost en GPU) | ✅ Código probado con un dataset de desarrollo; falta entrenarlo con los 397 puntos | Sección 6 |
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

El comando sortea puntos sobre píxeles de **cultivo**, con semilla fija (`--semilla 7`). El archivo `configs/puntos.csv` **sí se versiona**, para que cualquiera reproduzca el mismo dataset.

- **Cultivo** = MODIS Land Cover (IGBP 12 y 14, 500 m) **o** ESA WorldCover (clase 40, 10 m). MODIS solo ve el cultivo extensivo; WorldCover agrega las parcelas pequeñas de ladera.
- **Distancia mínima** de 6 km en el Huila y 15 km en el resto, para no repetir celda de SMAP (9 km). Sin ella, la mediana al vecino más cercano era de 2 km.
- **Resultado: 397 puntos** (128 en el Huila y 269 en el resto), no 600. Con esas distancias el área agrícola de Colombia no da para más; bajar las distancias da más puntos, pero repetidos en la misma celda.
- Antes el comando usaba `sample(numPixels=...)`, que sorteaba en toda la región y descartaba casi todo: de 600 quedaban 46. Ahora usa `stratifiedSample`.

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

En Windows, para que siga aunque se cierre la terminal, lanzarla como proceso aparte con el registro en un archivo:

```powershell
$env:PYTHONIOENCODING = 'utf-8'
Start-Process .\.venv\Scripts\python.exe -ArgumentList '-u','-m','datos_tierra','masivo','--puntos','configs/puntos.csv' `
  -RedirectStandardOutput ..\data\raw\entrenamiento_log.txt -RedirectStandardError ..\data\raw\entrenamiento_errores.txt -WindowStyle Hidden
Get-Content ..\data\raw\entrenamiento_log.txt -Wait      # para seguirla
```

**Si SoilGrids está caído** (cada punto se queda ~13 min esperando sus reintentos), bajar primero solo el clima y completar el suelo después:

```bash
python -m datos_tierra masivo --puntos configs/puntos.csv --fuentes power,smap,imerg,modis   # clima: ~19 s por punto
python -m datos_tierra suelo                 # cuando la API vuelva: suelo completo (con cuantiles y agua retenida)
python -m datos_tierra suelo --via gee       # o ya, con los mismos mapas en Earth Engine: ~5 s por punto
```

Con `--via gee` el suelo sale de `projects/soilgrids-isric` en Earth Engine: los mismos mapas, pero solo la media (sin Q0.05/Q0.95, así que sin incertidumbre) y sin `wv0033`/`wv1500`. El oráculo no los necesita: el agua del suelo sale de Saxton & Rawls. Ojo: en Earth Engine el nitrógeno viene en mg/kg, no en cg/kg como en la API; `fuentes/soilgrids_gee.py` ya lo convierte.

- Se crea un `data/raw/entrenamiento/<id>.json.gz` por punto. `data/raw/` no se versiona.
- **Se puede reanudar:** si se corta, se vuelve a lanzar el mismo comando y se salta lo que ya existe. A los puntos sin suelo (SoilGrids falló o no se pidió) solo se les pide el suelo.
- Si falla una fuente de clima (POWER, SMAP, IMERG o MODIS), el punto no se guarda y se repite completo en la siguiente corrida.
- Cada fuente se recorta sola a su cobertura: POWER desde 1981, IMERG desde 2000, SMAP desde 2015.
- Tiempo medido en esta máquina: **~19 s por punto** con POWER, SMAP, IMERG y MODIS de 1981 a 2025, es decir **~2 horas** para los 397. SoilGrids por la API agrega de 1 a 13 min por punto según cómo esté el servicio; por Earth Engine, ~5 s.
- Si un punto falla, el error queda en pantalla y la descarga sigue con el siguiente.

## 5. El catálogo de cultivos en esta máquina

Para entrenar **no hace falta MongoDB**: el oráculo lee directamente `data/catalogo_cultivos_mongodb/datos/cultivos.json`, que es el mismo contenido de `surco_agro`. Si se quiere tener la base local:

```bash
cd data/catalogo_cultivos_mongodb
mongosh "mongodb://localhost:27017" scripts/01_crear_base.js
mongosh "mongodb://localhost:27017" scripts/02_cargar_datos.js
```

## 6. Oráculo, dataset y modelo A

Detalle del diseño en [ml/README.md](README.md). Todo está en `ml/surco_ml/` y se ejecuta desde `ml/`:

```bash
python -m surco_ml.dataset                    # oráculo + features de los puntos descargados (~1 s por punto, reanudable)
python -m surco_ml.modelos.gbdt               # modelo A, corte por tiempo: 1981-2014 / 2015-2018 / prueba 2019-2024
python -m surco_ml.modelos.gbdt --sin-huila   # corte por espacio: entrena sin el Huila y prueba en el Huila
mlflow ui --backend-store-uri sqlite:///mlflow.db   # resultados en http://localhost:5000
python -m surco_ml.modelos.gbdt --solo-registrar    # registra en MLflow una corrida ya entrenada (con --sin-huila, la otra)
python -m surco_ml.predecir --finca pitalito-cafe --fecha 2023-03-01   # predicción para un lote; si el ciclo ya pasó, la compara con lo real
```

| Archivo | Qué hace | Cómo se comprobó |
|---|---|---|
| `surco_ml/catalogo.py` | Lee `cultivos.json` (el mismo de Mongo) en arreglos para Numba y como features del cultivo (`c_*`) | 44 cultivos; 37 con Kc y p para el balance |
| `surco_ml/series.py` | JSON de un punto → arreglos diarios. Solo columnas corregidas (`derived_t2m*_corr`, `derived_precip_mm`, `derived_et0_mm`) | |
| `surco_ml/suelo_motor.py` | TAW a la raíz de cada cultivo con Saxton & Rawls del motor agronómico (no hay una segunda versión) | |
| `surco_ml/oraculo/simulador.py` | Fases según `duracion_dias`, trapecios por fase y balance hídrico diario en secano y con riego automático. Numba en paralelo | Cada fase puntúa igual que `ejemplo_modelo.py`; **el maíz en Neiva sale mal en floración**; balance idéntico al de `formulas.py` |
| `surco_ml/oraculo/etiquetas.py` | 24 fechas × 44 años × 44 cultivos por punto, más la **línea base de climatología** y la frecuencia histórica de éxito | |
| `surco_ml/features/construir.py` | 94 features del día de la siembra (`f_*`): ventanas de 30/90/365 días, SMAP, IMERG, climatología futura, ENSO, suelo, sitio y fecha. Con las 36 del cultivo (`c_*`) y la TAW del lote-cultivo, el modelo ve 131 | **Prueba de fuga**: alterar el clima desde la siembra no cambia ninguna feature de esa fila |
| `surco_ml/dataset.py` | Parquet por punto en `data/processed/dataset/` (no se versiona) | |
| `surco_ml/modelos/gbdt.py` | XGBoost en GPU con `QuantileDMatrix` por lotes: puntaje y riego (p10/p50/p90), éxito y días de estrés; métricas contra la línea base, SHAP, MLflow y `.ubj` | Probado de punta a punta con un dataset de desarrollo de 12 puntos |
| `surco_ml/evaluacion/metricas.py` | MAE, pinball, cobertura, Brier, ECE y NDCG@3 | |
| `surco_ml/modelos/calibracion.py` | Isotónica para P(éxito) e intervalos conformales por tipo de ciclo, ajustados con la validación 2015-2018 | Pruebas con datos sintéticos: 10 % en cada cola |

**Si se corta la luz o se cierra el proceso**, volver a lanzar el mismo comando:
- Cada modelo se guarda apenas termina, con una firma de lo que lo produjo (`avance.json`): los que ya estaban se cargan y solo se entrena lo que faltaba. Si cambian los parámetros, el dataset o el catálogo, la firma no coincide y se reentrena.
- Cada prueba de Optuna queda en `modelos_exportados/optuna.db`: `--optuna 12` continúa desde la última prueba hecha.
- La preparación de las matrices (~12 min) sí se repite.

Decisiones del oráculo que conviene conocer (todas en el código, con su razón):
- **Falla crítica** (`exito = 0`): alguna fase por debajo de `UMBRAL_FALLA = 0,4`. Es un supuesto a calibrar en la etapa 4.
- **Riego**: el puntaje es de secano (lluvia contra el trapecio). `arroz_riego` es la excepción (`catalogo.CON_RIEGO`): su agua está asegurada y lo que mide es `riego_mm`.
- **Climatología sin fuga**: deja fuera el año de la siembra **y el siguiente**, porque la piña y los perennes siguen en el campo al año siguiente. La prueba de fuga encontró este caso.
- **Agotamiento inicial**: 60 días de arranque antes de la siembra, igual para todos los años (no depende de SMAP, que solo existe desde 2015).
- Los 7 cultivos sin Kc ni p tienen puntaje y éxito, pero `riego_mm` y `dias_estres` quedan vacíos.

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
