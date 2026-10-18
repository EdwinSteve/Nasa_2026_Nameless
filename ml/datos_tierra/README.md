# datos_tierra: servicio de datos del lote

Trae y unifica en un JSON todo lo que el motor agronómico y el modelo predictivo necesitan de un lote: clima diario de NASA POWER, humedad SMAP, lluvia IMERG, MODIS, suelo SoilGrids, elevación SRTM y El Niño (ONI).

Es la evolución de `scripts/data/external_apis/unificated.py` (PR #12): mantiene sus claves y columnas, y agrega lo que hacía falta para entrenar. Por qué se eligió cada dato: [estudio de datos](../../docs/datos/estudio-datos-modelo.md).

## Instalación

```bash
cd ml
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Solo para SMAP, IMERG y MODIS
export GEE_PROJECT="tu-proyecto"
python -c "import ee; ee.Authenticate()"
```

Sin `GEE_PROJECT` el servicio sigue funcionando: esas tres fuentes quedan con `status: skipped`.

## Uso

```bash
# Un lote: JSON para el motor o la demo
python -m datos_tierra lote --lat 3.22 --lon -75.22 --inicio 2024-01-01 --fin 2024-12-31 --climatologia

# Muchos puntos y 45 años: insumo del entrenamiento (un .json.gz por punto, reanudable)
python -m datos_tierra masivo --puntos ../data/fincas_demo.json --inicio 1981-01-01 --fin 2025-12-31

# Elegir los puntos de entrenamiento sobre zonas de cultivo (requiere GEE)
python -m datos_tierra puntos --n 450 --n-huila 150 --out configs/puntos.csv
```

| Opción | Descripción |
|---|---|
| `--fuentes` | `todas` (por defecto), `sin-gee`, o una lista: `power,soilgrids,dem,enso,smap,imerg,modis` |
| `--elevacion` | Elevación conocida del lote en m; si falta se consulta el DEM |
| `--climatologia` | Agrega la normal 1991-2020 por día del año |
| `--out` | `.json` o `.json.gz` |

Desde Python:

```python
from datos_tierra.unificar import ejecutar

async with httpx.AsyncClient(timeout=httpx.Timeout(300, connect=30)) as cliente:
    datos = await ejecutar(cliente, 3.22, -75.22, '2024-01-01', '2024-12-31', climatologia=True)
```

## Esquema 2.0

| Clave | Contenido |
|---|---|
| `schema_version`, `fetched_at`, `location`, `period` | Igual que en 1.0 |
| `sources` | Estado de cada fuente: `ok`, `error` o `skipped`, más sus metadatos |
| `site` | Elevación del lote y de la celda POWER, corrección de temperatura aplicada y cobertura MODIS |
| `soil` | `layers` (6 capas hasta 200 cm), `summary` (0-30, 0-60, 0-100 y 0-200 cm), `units`, `texture_sum_pct`, `empty` |
| `daily` | Una fila por día: `power_*`, `smap_*`, `imerg_precip_mm` y `derived_*` |
| `composites` | `modis_ndvi_16d` y `modis_lst_8d` |
| `enso` | ONI mensual desde 12 meses antes del inicio |
| `climatology` | 365 días con media, p10, p90 y probabilidad de día de lluvia |
| `quality` | `missing_days`, `outside_coverage_days` (antes de que existiera la misión) y `alerts` |
| `catalog_map` | Métrica del catálogo `surco_agro` → campo del JSON |

Columnas derivadas de `daily`:

| Columna | Qué es |
|---|---|
| `derived_t2m_corr`, `derived_t2m_max_corr`, `derived_t2m_min_corr` | Temperatura corregida por elevación (ADR 0002) |
| `derived_et0_mm`, `derived_et0_method` | ET0 FAO-56 Penman-Monteith; Hargreaves si falta radiación |
| `derived_et0_pm_mm`, `derived_et0_hargreaves_mm` | Los dos métodos por separado |
| `derived_vpd_kpa` | Déficit de presión de vapor |
| `derived_precip_mm`, `derived_precip_source` | IMERG si existe, si no POWER |
| `derived_evptrns_mm` | ET modelada de POWER pasada de MJ/m² a mm |

**Cambio que rompe con 1.0:** los valores de `soil` ya están en unidades convencionales (arcilla en %, pH en pH, N en g/kg, agua en m³/m³), no en las unidades crudas de SoilGrids. Ya no se dividen por `d_factor`.

## Rendimiento medido

| Fuente | Tiempo por punto |
|---|---|
| POWER, 45 años | ~3 s |
| DEM, ONI | <1 s (en el modo masivo se piden una sola vez) |
| SoilGrids, 12 propiedades × 6 capas | 1 a 10 min, según los reintentos de la API; es estático: se guarda y no se vuelve a pedir |
| SMAP, IMERG, MODIS | Sin medir (requiere GEE) |

## Pruebas

```bash
cd ml && pytest
```

Las pruebas no usan red. Incluyen los ejemplos 8 y 18 de FAO-56 para Ra y ET0.
