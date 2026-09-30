# Inventario de datos: qué hay disponible y qué verificamos

> Verificado el **2026-09-30** con [`scripts/verificar_fuentes.py`](../../scripts/verificar_fuentes.py).
> Zona: Huila (bbox `-76.6, 1.5, -74.4, 3.9`), año de referencia 2024.
> Resultado crudo: [`data/processed/verificacion_huila_2024.json`](../../data/processed/verificacion_huila_2024.json).

## Resumen

| Fuente | Estado | Login | Cobertura Huila | Último dato | Uso en el proyecto |
|---|---|---|---|---|---|
| **NASA POWER** (API) | ✅ Probada, devuelve datos | No | Global, celda ~0.5°×0.625° | Casi tiempo real | Clima base: GDD, balance hídrico, ventana de siembra |
| **SoilGrids** (ISRIC) | ✅ Probada en puntos rurales | No | 250 m | Estática | pH, textura, carbono orgánico, N del suelo |
| **SMAP L3** `SPL3SMP_E` v006 | ✅ En catálogo | Earthdata | 366 gránulos/2024 (diario) | 2026-09-28 | Humedad superficial 9 km |
| **SMAP L4** `SPL4SMGP` v008 | ✅ En catálogo | Earthdata | 2929 gránulos/2024 (cada 3 h) | 2026-09-27 | Humedad de **zona radicular** (clave para cultivos) |
| **GPM IMERG Final** `GPM_3IMERGDF` v07 | ⚠️ Con retraso | Earthdata | 366/2024 | **2025-09-30** | Lluvia histórica de calidad |
| **GPM IMERG Late** `GPM_3IMERGDL` v07 | ✅ En catálogo | Earthdata | 366/2024 | 2026-09-28 | Lluvia reciente |
| **MODIS NDVI** `MOD13Q1` v061 | ✅ En catálogo | Earthdata | 24/2024 (16 días) | 2026-08-29 | Vigor de vegetación 250 m |
| **MODIS LST** `MOD11A2` v061 | ✅ En catálogo | Earthdata | 46/2024 (8 días) | 2026-09-14 | Temperatura de superficie 1 km (calor extremo) |
| **MODIS ET** `MOD16A2GF` v061 | ⚠️ Con retraso | Earthdata | 46/2024 | 2025-12-27 | Evapotranspiración histórica 500 m |
| **HLS Landsat** `HLSL30` v2.0 | ⚠️ Mucha nube | Earthdata | 668/2024, **solo 57 con ≤30 % de nubes** | 2026-09-23 | NDVI por parcela 30 m |
| **HLS Sentinel-2** `HLSS30` v2.0 | ⚠️ Mucha nube | Earthdata | 967/2024, **solo 73 con ≤30 % de nubes** | 2026-09-27 | NDVI por parcela 30 m |
| **ECOSTRESS ESI** `ECO_L4T_ESI` v002 | ✅ En catálogo | Earthdata | 113/2024 (irregular) | 2026-09-19 | Estrés hídrico de la planta ~70 m |
| **ECOSTRESS ET** `ECO_L3T_JET` v002 | ✅ En catálogo | Earthdata | 113/2024 | 2026-09-19 | ET ~70 m |
| **MODIS Land Cover** `MCD12Q1` v061 | ✅ En catálogo | Earthdata | Anual | 2024 | Identificar zonas de cultivo |
| **GRACE-FO** mascons (JPL) | ✅ En catálogo | Earthdata | ~300 km, mensual | En curso | Narrativa de acuíferos (solo contexto, muy gruesa para una finca) |
| **GLDAS / FLDAS** | ✅ En catálogo | Earthdata | 0.25° / 0.1°, mensual | En curso | Alternativa modelada de humedad/ET si SMAP falla |

**"En catálogo"** = confirmamos en CMR que hay gránulos sobre el Huila, pero **todavía no hemos descargado ni abierto el archivo** (requiere cuenta de Earthdata). Ese es el siguiente paso.

## ⚠️ Hallazgos que afectan el diseño

### 1. POWER subestima la temperatura del valle en ~7 °C
La celda de POWER promedia el valle del Magdalena con la cordillera:

| Punto | Elevación real | Elevación de la celda POWER | T2M anual POWER | T2M corregida (−6.5 °C/km) |
|---|---|---|---|---|
| Neiva (casco urbano) | ~440 m | 1403 m | 20.25 °C | ~26.5 °C |
| Campoalegre (zona arrocera) | ~525 m | 1609 m | 19.19 °C | 26.2 °C |
| Pitalito (zona cafetera) | ~1320 m | 2121 m | 15.57 °C | 20.8 °C (la real ronda 19–20 °C, verificar) |

La media real de Neiva está alrededor de 27–28 °C. **Si usamos POWER sin corregir, el motor calcularía mal los GDD y descartaría cultivos de clima cálido que sí se dan.** Esto afectaría directamente el criterio de Validity.

**Mitigación (ya implementada en `descargar_power.py`):** columnas `*_corr` con corrección por gradiente térmico. **Pendiente:** validar contra MODIS LST (1 km) o estaciones del IDEAM, y usar un DEM (SRTM/Copernicus) para la elevación real en lugar de valores aproximados.

**Argumento para los jueces:** mostrar esta corrección suma puntos de Validity, porque demuestra que entendemos las limitaciones del dato.

### 2. La precipitación de POWER también es de celda gruesa
El promedio anual es ~1121 mm en la celda de Campoalegre. Hay que contrastarlo con IMERG (~11 km). Una opción complementaria es CHIRPS (5 km, no NASA, pero muy usado en Colombia).

### 3. SoilGrids devuelve vacío en zonas urbanas
En el centro de Neiva todos los valores salen `null`. En puntos rurales funciona. Ejemplo en Campoalegre (0–5 cm): pH 5.5, arcilla 26 %, arena 44 %, SOC 41 g/kg, N 2.55 g/kg.
→ Suelo ácido: relevante para elegir leguminosas (el fríjol tolera pH ≥ 5.5 con dificultad; la soya prefiere 6–7).

### 4. El Huila es muy nublado: las imágenes ópticas de 30 m son escasas
En 2024 solo ~8 % de las escenas HLS tienen ≤30 % de nubes. Implicaciones:
- No depender de una sola imagen: usar **compuestos** (mediana por temporada) y la máscara `Fmask`.
- Para series de vegetación, MODIS NDVI (compuesto de 16 días) es más confiable.
- Si hace falta ver a través de las nubes: Sentinel-1 SAR (ESA, disponible en GEE). Queda fuera del alcance inicial.

### 5. Latencias
- IMERG **Final** llega hasta 2025-09 → para meses recientes, usar **Late**.
- MODIS ET gap-filled llega hasta 2025-12.
- Para el demo, esto es irrelevante si usamos histórico (2015–2024) + climatología.

### 6. SMAP es de 9 km
Sirve como indicador regional de humedad, no por parcela. **SPL4SMGP** tiene zona radicular (0–100 cm), que es lo que importa para el cultivo.

## Qué falta verificar (siguiente paso)

- [ ] Crear cuenta Earthdata → `~/.netrc` → probar `earthaccess` descargando 1 gránulo de SPL4SMGP y 1 de MOD13Q1 para el Huila.
- [ ] Crear/registrar proyecto de Google Earth Engine → probar las mismas colecciones vía GEE (suele ser más rápido para extraer series por punto).
- [ ] Probar **AppEEARS** (extracción por punto sin descargar tiles completos).
- [ ] Extraer serie 2015–2024 de SMAP raíz + NDVI + LST para las 4 fincas demo.
- [ ] Validar la corrección de temperatura de POWER contra MODIS LST.
- [ ] Obtener elevación real de cada finca con un DEM.
- [ ] Buscar datos de estaciones IDEAM (datos abiertos Colombia) para validación.
- [ ] Buscar datos de área/rendimiento por cultivo en el Huila (Agronet / EVA del MADR) para anclar el impacto.

## Cómo reproducir

```bash
python scripts/verificar_fuentes.py                      # reporte en consola
python scripts/verificar_fuentes.py --lat 3.22 --lon -75.22 --elev 430
python scripts/descargar_power.py --inicio 2015 --fin 2024   # CSVs en data/raw/power/
```
