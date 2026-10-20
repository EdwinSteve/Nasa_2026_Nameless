# Estudio de datos para el modelo predictivo

> Fecha: 2026-10-17. Parte del [inventario de datos](inventario.md), del catálogo `surco_agro` y de la [arquitectura del modelo](../../ml/README.md).
> Resultado: el servicio [`ml/datos_tierra`](../../ml/datos_tierra/README.md), que reemplaza a `scripts/data/external_apis/unificated.py` como fuente de datos del motor y del entrenamiento.

## 1. Qué tiene que traer el servicio

El modelo predice cómo puntuará cada cultivo del catálogo con el clima que ocurra durante su ciclo. Por eso el servicio tiene que entregar tres tipos de datos:

| Tipo | Para qué | Ejemplo |
|---|---|---|
| **Lo que compara el catálogo** | Las etiquetas del oráculo: cada fase contra sus trapecios | T2M de la fase contra `temperatura_aire_C` |
| **Lo que necesita el balance hídrico** | ET0, ETc, TAW, agotamiento y Ks (informe 08, 4.2 a 4.15) | Radiación, punto de rocío, textura, humedad SMAP |
| **Lo que se sabe el día de la siembra** | Las features del modelo | Clima de los 365 días previos, ENSO, climatología |

## 2. Qué traía el motor de datos v1 y qué faltaba

| Dato | Para qué lo usa SURCO | v1 (`unificated.py`) | v2 (`datos_tierra`) |
|---|---|---|---|
| **T2M** (temperatura media) | Trapecio `temperatura_aire_C` de cada fase | ❌ No se pedía | ✅ |
| T2M_MAX, T2M_MIN | Calor crítico en floración, ET0 | ✅ | ✅ |
| **Corrección por elevación** (ADR 0002) | Que el valle no salga 6–7 °C más frío | ❌ Solo guardaba la elevación de la celda | ✅ `derived_t2m*_corr` |
| **Elevación real del lote** (DEM) | La corrección y la métrica `altitud_msnm` | ❌ | ✅ SRTM 30 m |
| **T2MDEW** (punto de rocío) | Presión de vapor real para ET0 | ❌ | ✅ |
| PRECTOTCORR, RH2M, WS2M | Trapecios de lluvia, humedad y viento | ✅ | ✅ |
| **WS2M_MAX** | Ráfagas: caída de flores (riesgo del catálogo) | ❌ | ✅ |
| ALLSKY_SFC_SW_DWN | ET0 | ✅ | ✅ |
| **CLRSKY_SFC_SW_DWN, PAR** | Nubosidad y radiación para el crecimiento | ❌ | ✅ |
| GWETROOT | Humedad de raíz modelada, existe desde 1981 (SMAP solo desde 2015) | ✅ | ✅ más GWETTOP y GWETPROF |
| **PS, QV2M, TS, EVPTRNS** | Presión, humedad específica, temperatura de superficie, ET modelada | ❌ | ✅ |
| **ET0 FAO-56** | ETc = Kc × ET0: el motor la recibía ya calculada pero nadie la calculaba | ❌ | ✅ Penman-Monteith + Hargreaves de respaldo |
| SMAP `sm_surface`, `sm_rootzone` | Agotamiento inicial (4.13) | ✅ | ✅ más `sm_profile` y ET real |
| IMERG | Lluvia a 11 km, mejor que la celda de POWER | ✅ | ✅ más fusión con POWER |
| **Lluvia fusionada** | Una sola columna de lluvia para el oráculo | ❌ | ✅ `derived_precip_mm` con su fuente |
| SoilGrids textura, SOC, pH, CEC, N, CFVO, densidad | Saxton & Rawls, TAW, trapecios de pH y `N_O_CUL` | ✅ hasta 100 cm, en unidades crudas | ✅ hasta **200 cm**, en unidades convencionales |
| **SoilGrids `wv0033`, `wv1500`** | Agua a capacidad de campo y marchitez **estimada por ISRIC**: contraste de Saxton & Rawls | ❌ | ✅ en m³/m³ |
| **Promedios hasta la raíz** | El suelo a la profundidad Zr de cada cultivo (4.7) | ❌ | ✅ 0-30, 0-60, 0-100 y 0-200 cm, más una función para cualquier Zr |
| **ENSO (ONI)** | La principal fuente de predictibilidad del clima en Colombia | ❌ | ✅ |
| **Climatología por día del año** | Lo que el modelo sabe de los próximos meses al sembrar | ❌ | ✅ 1991-2020, media, p10, p90 y probabilidad de lluvia |
| **MODIS NDVI/EVI** | Vigor (4.16) y verificación de que hubo cultivo | ❌ | ✅ compuestos de 16 días |
| **MODIS LST** | Calor extremo y validación de la corrección de temperatura | ❌ | ✅ compuestos de 8 días |
| **MODIS Land Cover** | Saber si el punto es zona de cultivo; elegir puntos de entrenamiento | ❌ | ✅ |
| Rangos largos (décadas) | Entrenamiento con 1981–2025 | ⚠️ `getInfo()` con límite de 5000 días | ✅ bloques de 1000 días en paralelo |
| Muchos puntos | Entrenamiento con ~600 puntos | ❌ | ✅ modo `masivo` reanudable |

## 3. Prioridad de las fuentes

Partiendo del ranking del [informe 08](../investigacion/08_INFORME_FUENTES_Y_FORMULAS.md#2-ranking-de-fuentes) y del inventario:

**Núcleo, sin credenciales** (se descarga siempre):
1. **NASA POWER**: 18 variables desde 1981, la única serie diaria larga y continua. Es el esqueleto del dataset.
2. **SRTM (DEM)**: sin la elevación real todo lo térmico queda mal.
3. **SoilGrids**: el suelo, estático, se pide una sola vez por punto.
4. **ONI (NOAA)**: no es NASA, pero sin él el modelo no tiene cómo anticipar El Niño y La Niña.

**Satelital, requiere Earth Engine** (sube la *Relevance* y la resolución):

5. **SMAP L4**: la fuente de mayor puntaje del informe (93). Solo existe desde 2015, así que el modelo la usa con una bandera de disponibilidad.
6. **GPM IMERG V07**: lluvia a 11 km desde el 2000.
7. **MODIS** NDVI, LST y Land Cover: verificación, calor y selección de puntos.

**Descartadas por ahora**, con la razón del inventario:

| Fuente | Por qué no |
|---|---|
| HLS 30 m | Solo ~8 % de las escenas del Huila tienen ≤30 % de nubes |
| ECOSTRESS | Pasadas irregulares, no sirve como serie |
| GRACE-FO | ~300 km: solo sirve como narrativa de acuíferos |
| MODIS ET (MOD16) | Llega con meses de retraso; la ET0 calculada y la de SMAP la cubren |
| CHIRPS | Buena lluvia a 5 km, pero no es NASA; candidata si IMERG falla |

## 4. Hallazgos verificados en vivo (2026-10-17)

| Hallazgo | Valor |
|---|---|
| POWER entrega **18 variables × 45 años en una sola petición** | 16 436 días en ~4 s (4,9 MB) |
| La radiación de POWER **empieza en 1984** | 1095 días vacíos en 1981–1983 → en esos días la ET0 es Hargreaves |
| Elevación real de Villavieja | **385 m** en SRTM (`fincas_demo.json` decía 430 m); celda POWER a 1403 m |
| Corrección de temperatura en Villavieja | **+6,62 °C**: la máxima de agosto pasa de 26,4 a **33,1 °C**, coherente con la Tatacoa |
| ET0 Penman-Monteith en Villavieja, 2024 | 5,1 mm/día de media; Hargreaves da valores parecidos (4,9 frente a 5,0 el 8 de agosto) |
| `EVPTRNS` de POWER viene en **MJ/m²/día**, no en mm | Se convierte con 2,45 MJ/mm → `derived_evptrns_mm` |
| SoilGrids sí tiene **agua retenida** (`wv0033`, `wv1500`) | Villavieja 0-30 cm: θ33 = 0,34 y θ1500 = 0,16 m³/m³ |
| Suma de textura con la media | 100 % en todas las capas (con cuantiles daba de 7,7 % a 243 %) |
| La incertidumbre de SoilGrids es alta en el Huila | Arcilla: intervalo 90 % de 3 veces la mediana → va como feature |
| SoilGrids tarda **~1 minuto** por punto con todas las capas | 600 puntos ≈ 10 h; se hace una vez y se guarda |
| ONI actual | +2,16 en JAS 2026: **El Niño fuerte en curso** |
| Earth Engine (SMAP, IMERG, MODIS) | **No se probó en vivo**: esta máquina no tiene credenciales. El código maneja la falta de credenciales y queda como `skipped` |

## 5. Métricas del catálogo `surco_agro` → campos del JSON

| Métrica del catálogo | Campo | Cómo se compara |
|---|---|---|
| `temperatura_aire_C` | `daily.derived_t2m_corr` (+ `_max_corr`) | Media de la fase contra el trapecio; días con máxima sobre `temp_max_critica_C` |
| `precipitacion_mm` | `daily.derived_precip_mm` | Suma de la fase contra el trapecio |
| `precipitacion_mm_dia` | `daily.derived_precip_mm` | Media diaria de la fase |
| `humedad_relativa_pct` | `daily.power_rh2m` | Media de la fase |
| `viento_2m_ms` | `daily.power_ws2m` (y `power_ws2m_max`) | % de días sobre `max_tolerable` |
| `kc` | `daily.derived_et0_mm` | ETc = Kc × ET0 |
| `agotamiento_permitido_p` | `daily.smap_sm_rootzone` + `soil.layers.*.wv0033/wv1500` | Agotamiento contra p × TAW |
| `N_O_CUL` | `soil.summary.0-30cm.nitrogen` (g/kg) | Contra el trapecio |
| `ph` | `soil.summary.0-30cm.phh2o` | Contra el trapecio |
| `altitud_msnm` | `site.elevation_m` | Dentro del rango de la zona de producción |

El JSON trae esta tabla en `catalog_map` para que el motor no tenga que adivinarla.

## 6. Pendientes para otros equipos

- **Catálogo:** de los 12 cultivos sin Kc, Zr ni p, 5 se completaron con un análogo de su familia (arracacha, mora, lulo, uchuva y crotalaria). Los otros 7 (ñame, mango, guayaba, papaya, maracuyá, granadilla y tomate de árbol) **siguen sin dato** porque no hay un pariente defendible en FAO-56. Detalle y fuentes sugeridas en el [README del catálogo](../../data/catalogo_cultivos_mongodb/README.md#9-valores-aproximados-por-análogo).
- **Motor agronómico:** `normalizer.py` espera las unidades crudas de SoilGrids. Con el esquema 2.0 los valores ya vienen convertidos: arena y arcilla en %, que se pasan a fracción dividiendo por 100, y SOC en g/kg. Hay que ajustar el `normalizer.py` o usar `soil.summary`.
- **Datos:** probar SMAP, IMERG y MODIS con una cuenta de Earth Engine (`GEE_PROJECT`) y medir cuánto tarda un punto de 10 años.
- **Validación:** contrastar `derived_t2m_max_corr` con MODIS LST y con estaciones del IDEAM, como pide la ADR 0002.
- **Supuesto a revisar:** la presión de vapor sale del punto de rocío de la celda, sin corregir por elevación; en el valle la ET0 puede quedar ligeramente sobrestimada.
