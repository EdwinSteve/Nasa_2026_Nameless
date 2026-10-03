# Informe de investigación: fuentes de datos, fórmulas e impacto en el proyecto

**Proyecto:** SURCO — NASA Space Apps Challenge 2026, reto *Field Shift: Adapting Farms with NASA Data*
**Ejes:** rotación de cultivos y optimización de los recursos hídricos
**Fecha:** 28 de septiembre de 2026

---

## 0. Resumen ejecutivo

En esta etapa revisamos las fuentes de datos que vamos a usar, verificamos cuáles son las más limpias y evaluamos cuánto aporta cada una al proyecto y a los cinco criterios de evaluación del hackathon (Impact, Creativity, Validity, Relevance, Presentation).

Las conclusiones principales son:

1. Íbamos por buen camino con **NASA POWER** y **SoilGrids**, pero teníamos tres imprecisiones: la radiación solar no se mide a 2 metros, SoilGrids no entrega profundidad del suelo y su nitrógeno es nitrógeno total, no disponible para la planta.
2. La profundidad de raíz no la da el suelo sino el cultivo (tabla 22 de FAO-56). Al combinarla con la textura de SoilGrids obtenemos el **agua que el suelo puede guardar para cada cultivo**, que es el puente entre rotación y ahorro de agua.
3. Con solo POWER y SoilGrids el criterio de *Relevance* queda débil, porque SoilGrids no es de la NASA. Las dos fuentes con mayor impacto resultaron ser **SMAP L4** (93/100) y **NASA POWER** (80/100).
4. Definimos un conjunto mínimo de **seis datos** que mueven todas las decisiones del MVP y descartamos del MVP las fuentes de baja limpieza para nuestra escala (ECOSTRESS) o de resolución insuficiente para un lote (GRACE-FO).
5. En un ejemplo ilustrativo, pasar de riego por calendario fijo a riego basado en el balance hídrico reduce la lámina aplicada en maíz de 680 mm a unos 306 mm por ciclo (cerca de 3.700 m³ por hectárea), lo que muestra el tamaño del impacto que podemos cuantificar en la demo.

---

## 1. Metodología de evaluación

### 1.1 Criterios
Calificamos cada fuente de 0 a 3 en cada uno de los cinco criterios del hackathon:

| Puntaje | Significado |
|---|---|
| 0 | No aporta al criterio |
| 1 | Aporte indirecto o menor |
| 2 | Aporte claro |
| 3 | Aporte central: sin esta fuente el criterio se debilita mucho |

Qué evaluamos en cada criterio:

| Criterio | Pregunta que nos hicimos |
|---|---|
| Impact | ¿Mueve una decisión que cambia agua, dinero o suelo del campesino? |
| Creativity | ¿Permite una funcionalidad que otros equipos no tienen? |
| Validity | ¿Es científicamente sólida, documentada y con incertidumbre conocida? |
| Relevance | ¿Es un dato de la NASA y es esencial (no decorativo)? |
| Presentation | ¿Se puede mostrar de forma visual y entendible en la demo? |

### 1.2 Índice de relevancia y factor de limpieza

```
Relevancia (0–100) = (suma de los 5 puntajes / 15) × 100
Prioridad final     = Relevancia × Factor de limpieza
```

El factor de limpieza castiga las fuentes difíciles de usar a la escala de un lote o en el tiempo del hackathon:

| Factor | Cuándo se aplica |
|---|---|
| 1,0 | Sin huecos, serie larga, acceso directo |
| 0,9 | Limpia, pero con resolución o incertidumbre que hay que comunicar |
| 0,75 | Útil, pero con huecos frecuentes (nubes) que exigen procesamiento extra |
| 0,5 | Pasadas irregulares o resolución que no sirve para un lote |

### 1.3 Niveles de relevancia

| Nivel | Prioridad final | Tratamiento en el proyecto |
|---|---|---|
| Crítico | 75 o más | Núcleo del MVP, se implementa primero |
| Alto | 50 a 74 | Parte del MVP |
| Medio | 30 a 49 | Respaldo o contexto |
| Bajo | menos de 30 | Fuera del MVP; visión futura |

---

## 2. Ranking de fuentes

| Fuente | Impact | Creat. | Valid. | Relev. | Present. | Relevancia | Limpieza | Prioridad | Nivel |
|---|---|---|---|---|---|---|---|---|---|
| SMAP L4 (humedad del suelo) | 3 | 2 | 3 | 3 | 3 | 93 | 1,0 | 93 | Crítico |
| NASA POWER (clima) | 3 | 1 | 3 | 3 | 2 | 80 | 1,0 | 80 | Crítico |
| Profundidad de raíz y factor p (FAO-56) | 3 | 2 | 3 | 1 | 2 | 73 | 1,0 | 73 | Alto |
| GPM IMERG (lluvia) | 2 | 1 | 3 | 3 | 2 | 73 | 1,0 | 73 | Alto |
| MODIS NDVI 16 días | 2 | 1 | 2 | 3 | 3 | 73 | 0,9 | 66 | Alto |
| HLS NDVI 30 m (vigor del lote) | 2 | 3 | 1 | 3 | 3 | 80 | 0,75 | 60 | Alto |
| SoilGrids (suelo) | 3 | 1 | 3 | 1 | 1 | 60 | 0,9 | 54 | Alto |
| POWER GWETROOT (respaldo de humedad) | 1 | 0 | 2 | 2 | 0 | 33 | 1,0 | 33 | Medio |
| GRACE-FO (agua regional) | 1 | 1 | 2 | 2 | 3 | 60 | 0,5 | 30 | Medio |
| ECOSTRESS (estrés de la planta) | 1 | 2 | 1 | 3 | 1 | 53 | 0,5 | 26 | Bajo |

### 2.1 Lectura del ranking

- **SMAP y POWER son el núcleo.** Juntas cubren el estado actual del agua y toda la historia climática, y son de la NASA. Sin ellas no hay proyecto.
- **SoilGrids tiene prioridad media-alta aunque su impacto es máximo.** Su puntaje baja porque no es de la NASA y se ve poco en la demo, pero es un **habilitador**: sin la textura del suelo no se puede calcular cuánta agua guarda el lote. Por eso se mantiene en el MVP.
- **La tabla de raíces de FAO-56 es tan importante como IMERG.** No es un dato satelital, pero es lo que convierte la humedad y la textura en una decisión de riego por cultivo.
- **HLS es la fuente más creativa** (seguimiento del lote a 30 m), pero las nubes de Huila le bajan el factor de limpieza. MODIS es su respaldo.
- **ECOSTRESS y GRACE-FO quedan fuera del MVP.** GRACE-FO se usa solo como contexto visual en el pitch.

---

## 3. Fichas por fuente (en orden de prioridad)

### 3.1 SMAP L4 — Humedad del suelo (Crítico, 93)

| Aspecto | Detalle |
|---|---|
| Qué es | Producto de nivel 4 de la misión SMAP de la NASA: combina la observación satelital de microondas con un modelo de superficie terrestre |
| Variables | Humedad superficial (0–5 cm) y de zona radicular (0–100 cm), en m³/m³ |
| Resolución | ~9–11 km, cada 3 horas |
| Acceso | Google Earth Engine (`NASA/SMAP/SPL4SMGP/...`, verificar versión), Earthdata |
| Limpieza | Alta: al ser un producto de modelo con asimilación, no tiene huecos |
| Para qué sirve | Punto de partida del balance hídrico: cuánta agua tiene hoy la tierra; si un cultivo aguanta en secano; alerta de riego |
| Impacto en el proyecto | Es el dato que más decisiones de agua mueve y el que mejor demuestra *Relevance*: "SMAP dice 0,12 → no recomendamos maíz en secano" |

### 3.2 NASA POWER — Clima (Crítico, 80)

| Aspecto | Detalle |
|---|---|
| Qué es | Servicio de la NASA que empaqueta datos de clima (reanálisis MERRA-2) y radiación (CERES/GEWEX) listos para usar |
| Resolución | 0,5° × 0,625° para meteorología (~55 km); 1° para radiación |
| Serie | Diaria desde 1981 |
| Acceso | API REST sin autenticación, JSON |
| Limpieza | Alta: sin huecos en la serie histórica; los últimos días pueden venir con -999 por latencia |
| Para qué sirve | Grados-día, evapotranspiración, años análogos para el modelo predictivo, aptitud térmica |

**Corrección respecto a lo que teníamos:** la radiación solar no se mide a 2 metros; se reporta en la superficie. A 2 metros se miden temperatura, humedad y viento. Las variables correctas son:

| Variable | Qué es | Unidad (community=AG) | Decisión que mueve |
|---|---|---|---|
| T2M_MAX, T2M_MIN | Temperatura máxima y mínima a 2 m | °C | Fecha de cosecha (grados-día), calor en floración |
| PRECTOTCORR | Lluvia diaria con corrección de sesgo | mm/día | Cuánto regar |
| RH2M | Humedad relativa a 2 m | % | Evapotranspiración |
| WS2M | Viento a 2 m | m/s | Evapotranspiración |
| ALLSKY_SFC_SW_DWN | Radiación solar en superficie | MJ/m²/día | Evapotranspiración |
| GWETROOT | Humedad relativa de la zona de raíces (0 a 1) | adimensional | Respaldo de SMAP |

Usamos `community=AG` porque entrega la radiación en MJ/m²/día, la unidad que pide la fórmula de Penman-Monteith. Con `community=RE` llega en kWh/m²/día.

### 3.3 Profundidad de raíz y factor p — FAO-56 (Alto, 73)

| Aspecto | Detalle |
|---|---|
| Qué es | Valores tabulados por la FAO (Boletín 56, tabla 22) de profundidad efectiva de raíz y fracción de agua que el cultivo puede agotar sin estrés |
| Para qué sirve | Define hasta qué profundidad del suelo "cuenta" el agua para cada cultivo y cada cuánto hay que regar |
| Impacto | Es lo que hace que la rotación cambie el uso del agua: el mismo suelo y la misma lluvia dan intervalos de riego distintos según el cultivo |

Valores de referencia que incorporamos al catálogo (rango FAO-56 y valor de trabajo):

| Cultivo | Raíz Zr (m), rango | Zr de trabajo | p |
|---|---|---|---|
| Maíz | 1,0 – 1,7 | 1,0 | 0,55 |
| Sorgo | 1,0 – 2,0 | 1,0 | 0,55 |
| Soya | 0,6 – 1,3 | 0,9 | 0,50 |
| Fríjol | 0,6 – 0,9 | 0,7 | 0,45 |
| Maní | 0,5 – 1,0 | 0,7 | 0,50 |
| Tomate | 0,7 – 1,5 | 0,8 | 0,40 |
| Yuca (primer año) | 0,5 – 0,8 | 0,6 | 0,35 |

El arroz inundado se maneja con un balance distinto (lámina de agua sobre el suelo) y se trata como caso especial.

### 3.4 GPM IMERG — Lluvia satelital (Alto, 73)

| Aspecto | Detalle |
|---|---|
| Qué es | Precipitación combinada de la constelación de satélites GPM |
| Resolución | ~10 km, cada 30 minutos |
| Versiones | Early y Late (rápidas, menos precisas) y Final (más precisa, con meses de retraso) |
| Limpieza | Alta |
| Uso | Final para el histórico y la validación; Late para los últimos días |
| Para qué sirve | Lluvia más cercana al lote que la de POWER; corrección de sesgo de POWER; anomalías de lluvia |

### 3.5 MODIS NDVI 16 días (Alto, 66)

| Aspecto | Detalle |
|---|---|
| Qué es | Índice de vegetación del sensor MODIS, compuesto cada 16 días (MOD13Q1) |
| Resolución | 250 m |
| Limpieza | Media-alta: el composite elige los mejores píxeles del periodo, con menos nubes |
| Para qué sirve | Historia de vigor del lote desde 2000, curvas fenológicas esperadas, respaldo de HLS |

### 3.6 HLS NDVI 30 m (Alto, 60)

| Aspecto | Detalle |
|---|---|
| Qué es | Landsat y Sentinel-2 armonizados por la NASA |
| Resolución | 30 m, cada 2–3 días combinando sensores |
| Limpieza | Media: nubes frecuentes en Huila; exige máscara de nubes (banda Fmask) y composites |
| Para qué sirve | Seguimiento del cultivo dentro del polígono del agricultor; días de suelo desnudo; time-lapse del lote |
| Impacto | Es la fuente que habilita nuestro diferencial principal (plan vivo hasta la cosecha) |

### 3.7 SoilGrids 2.0 — Suelo (Alto, 54)

| Aspecto | Detalle |
|---|---|
| Qué es | Mapas globales de propiedades del suelo de ISRIC, generados con aprendizaje automático |
| Resolución | 250 m |
| Capas | 0–5, 5–15, 15–30, 30–60, 60–100 y 100–200 cm |
| Licencia | CC-BY 4.0 |
| Limpieza | Alta en formato; incertidumbre variable según la zona |
| Para qué sirve | Aptitud de suelo (pH), capacidad de retener agua (textura, carbono, piedras), indicador de salud del suelo |

**Correcciones respecto a lo que teníamos:**

1. **SoilGrids no entrega profundidad del suelo.** Predice pH, texturas, fragmentos gruesos, densidad aparente, nitrógeno total, carbono orgánico y capacidad de intercambio catiónico. La profundidad del suelo figura como propiedad en desarrollo. La profundidad que usamos para los cálculos es la de la raíz del cultivo (sección 3.3).
2. **El nitrógeno es nitrógeno total**, no el disponible para la planta. Lo usamos como indicador de fertilidad y salud del suelo, nunca para recomendar dosis de fertilizante.
3. **Es un modelo, no una medición del lote.** Pedimos siempre los percentiles Q0.05, Q0.5 y Q0.95. Si el rango es muy ancho, el dato se marca como de baja confianza y la app sugiere un análisis de suelo. Si el agricultor carga un análisis de laboratorio, ese valor reemplaza al de SoilGrids.

Propiedades que pedimos y para qué:

| Propiedad | Qué mide | Para qué la usamos |
|---|---|---|
| sand, silt, clay | Arena, limo y arcilla | Capacidad de retener agua (Saxton y Rawls) |
| soc | Carbono orgánico | Retención de agua, salud del suelo |
| cfvo | Fragmentos gruesos (piedras) | Corrección del agua disponible |
| bdod | Densidad aparente | Compactación, conversión a existencias de carbono |
| phh2o | pH en agua | Filtro de aptitud por cultivo |
| cec | Capacidad de intercambio catiónico | Fertilidad general |
| nitrogen | Nitrógeno total | Indicador de salud del suelo |

### 3.8 POWER GWETROOT (Medio, 33)
Humedad relativa de la zona de raíces del modelo MERRA-2. Es más gruesa que SMAP y está expresada como fracción de saturación, no como contenido volumétrico. La dejamos como respaldo si Earth Engine falla durante la demo.

### 3.9 GRACE-FO (Medio, 30)
Mide cambios en el almacenamiento total de agua (incluidos acuíferos) con celdas de unos 300 km y frecuencia mensual. No sirve para un lote, pero muestra la tendencia del agua en la cuenca del Magdalena. La usamos solo como contexto en el pitch.

### 3.10 ECOSTRESS (Bajo, 26)
Mide evapotranspiración y estrés térmico de la planta a ~70 m desde la Estación Espacial Internacional, pero sus pasadas sobre un punto son irregulares. Queda fuera del MVP; es una mejora futura.

---

## 4. Fórmulas: qué son y para qué sirven

Cada fórmula tiene un propósito concreto dentro del motor. Los ejemplos usan valores típicos de Neiva para mostrar órdenes de magnitud.

### 4.1 Grados-día de crecimiento (GDD)

```
GDD_día = max(0, (min(Tmax, T_tope) + max(Tmin, T_base)) / 2 − T_base)
GDD_ciclo = Σ GDD_día
```

| Variable | Significado |
|---|---|
| Tmax, Tmin | Temperaturas diarias de POWER (°C) |
| T_base | Temperatura por debajo de la cual el cultivo no crece (10 °C en maíz) |
| T_tope | Temperatura por encima de la cual no crece más rápido (30 °C en maíz) |

**Para qué sirve:** estimar cuándo llega la cosecha según el clima real, en lugar de usar un número fijo de días. También define cuándo empieza cada etapa (floración, llenado).

**Ejemplo:** Tmax = 34 °C, Tmin = 22 °C, maíz → (30 + 22)/2 − 10 = **16 GDD** ese día.

### 4.2 Evapotranspiración de referencia (ET0) — FAO-56 Penman-Monteith

```
ET0 = [0,408 Δ (Rn − G) + γ (900 / (T + 273)) u2 (es − ea)] / [Δ + γ (1 + 0,34 u2)]
```

Ecuaciones auxiliares:

```
e°(T)  = 0,6108 · exp(17,27 T / (T + 237,3))                 presión de vapor de saturación (kPa)
es     = (e°(Tmax) + e°(Tmin)) / 2
ea     = (RH2M / 100) · es                                    presión real de vapor
Δ      = 4098 · e°(T) / (T + 237,3)²                          pendiente de la curva de vapor
P      = 101,3 · ((293 − 0,0065 z) / 293)^5,26                presión atmosférica según altitud z (m)
γ      = 0,000665 · P                                         constante psicrométrica
Rso    = (0,75 + 2·10⁻⁵ z) · Ra                               radiación en cielo despejado
Rns    = (1 − 0,23) · Rs                                      radiación neta de onda corta
Rnl    = σ · [(Tmax,K⁴ + Tmin,K⁴)/2] · (0,34 − 0,14 √ea) · (1,35 Rs/Rso − 0,35)
Rn     = Rns − Rnl
G      ≈ 0 a escala diaria
```

| Variable | Significado | Fuente |
|---|---|---|
| T | Temperatura media (°C) | POWER T2M |
| u2 | Viento a 2 m (m/s) | POWER WS2M |
| Rs | Radiación solar en superficie (MJ/m²/día) | POWER ALLSKY_SFC_SW_DWN |
| Ra | Radiación extraterrestre | Se calcula con latitud y día del año |
| z | Altitud del lote (m) | Modelo de elevación |
| σ | 4,903·10⁻⁹ MJ K⁻⁴ m⁻² día⁻¹ | Constante |

**Para qué sirve:** es la cantidad de agua que "pide" la atmósfera cada día. Es la base de todo el cálculo de riego.

**Ejemplo (16 de marzo, Neiva, z = 442 m):** Tmax = 34 °C, Tmin = 22 °C, humedad 65 %, viento 1,5 m/s, Rs = 19 MJ/m²/día → Ra = 37,7, Rn = 12,1 y **ET0 ≈ 4,7 mm/día**.

### 4.3 ET0 por Hargreaves (respaldo)

```
ET0 = 0,0023 · (0,408 · Ra) · (T + 17,8) · √(Tmax − Tmin)
```

**Para qué sirve:** cuando falta viento, humedad o radiación. Con los mismos datos del ejemplo da 5,6 mm/día, es decir, sobreestima frente a Penman-Monteith en clima húmedo. Por eso es solo respaldo y se marca en la procedencia.

### 4.4 Evapotranspiración del cultivo (ETc)

```
ETc = Kc(etapa) · ET0
```

**Para qué sirve:** ajusta la demanda de agua al cultivo y a su etapa. Un maíz en floración (Kc = 1,20) consume más que la referencia; recién sembrado (Kc = 0,30) consume mucho menos.

**Ejemplo:** fríjol en floración, Kc = 1,15 y ET0 = 4,7 → **ETc ≈ 5,4 mm/día**.

### 4.5 Precipitación efectiva (USDA-SCS, escala mensual)

```
Pe = P · (125 − 0,2 P) / 125      si P ≤ 250 mm/mes
Pe = 125 + 0,1 P                  si P > 250 mm/mes
```

**Para qué sirve:** no toda la lluvia queda disponible para la planta; parte se escurre o se infiltra por debajo de la raíz.

**Ejemplos:** 80 mm/mes → 69,8 mm efectivos; 200 mm → 136 mm; 300 mm → 155 mm.

### 4.6 Conversión de unidades de SoilGrids

```
valor_convencional = valor_SoilGrids / factor
```

| Propiedad | Unidad SoilGrids | Factor | Unidad convencional |
|---|---|---|---|
| phh2o | pH × 10 | 10 | pH |
| soc | dg/kg | 10 | g/kg |
| nitrogen | cg/kg | 100 | g/kg |
| bdod | cg/cm³ | 100 | kg/dm³ |
| cec | mmol(c)/kg | 10 | cmol(c)/kg |
| cfvo | cm³/dm³ | 10 | % volumen |
| sand, silt, clay | g/kg | 10 | % |

**Para qué sirve:** evitar errores silenciosos. Un pH de 65 sin convertir hace que el motor descarte todos los cultivos.

### 4.7 Promedio ponderado por espesor hasta la raíz

```
X̄ = Σ (x_i · h_i) / Σ h_i
```

`x_i` es el valor de la capa i y `h_i` su espesor dentro de la zona de raíz. La última capa se recorta a la profundidad de raíz.

**Para qué sirve:** convertir las seis capas de SoilGrids en un solo valor representativo para cada cultivo.

**Ejemplo para fríjol (Zr = 0,7 m):** capas 0–5 (5 cm), 5–15 (10), 15–30 (15), 30–60 (30) y 60–70 (10 cm de la capa 60–100).

### 4.8 Materia orgánica a partir del carbono

```
MO (%) = 1,724 · SOC (%)        con SOC (%) = SOC (g/kg) / 10
```

**Para qué sirve:** Saxton y Rawls piden materia orgánica, y SoilGrids entrega carbono orgánico. El factor 1,724 es el de van Bemmelen.

### 4.9 Humedad a capacidad de campo y punto de marchitez (Saxton y Rawls, 2006)

S = arena y C = arcilla en fracción (0 a 1); MO en %.

```
θ1500t = −0,024 S + 0,487 C + 0,006 MO + 0,005 (S·MO) − 0,013 (C·MO) + 0,068 (S·C) + 0,031
θ1500  = θ1500t + (0,14 θ1500t − 0,02)                                    punto de marchitez

θ33t   = −0,251 S + 0,195 C + 0,011 MO + 0,006 (S·MO) − 0,027 (C·MO) + 0,452 (S·C) + 0,299
θ33    = θ33t + (1,283 θ33t² − 0,374 θ33t − 0,015)                        capacidad de campo
```

**Para qué sirve:** estimar cuánta agua puede retener el suelo (capacidad de campo) y a partir de qué punto la planta ya no puede extraerla (marchitez).

**Ejemplo (suelo franco: 40 % arena, 20 % arcilla, 2,5 % MO):** θ33 = 0,280 y θ1500 = 0,137 → diferencia de **0,143 m³/m³**.

### 4.10 Agua total disponible (TAW) con corrección por piedras

```
TAW (mm) = 1000 · (θ33 − θ1500) · Zr · (1 − cfvo/100)
```

**Para qué sirve:** es el "tanque" de agua del suelo que el cultivo puede usar. Depende del suelo (textura y piedras) y del cultivo (raíz).

### 4.11 Agua fácilmente aprovechable (RAW)

```
RAW (mm) = p · TAW
```

**Para qué sirve:** es la parte del tanque que el cultivo puede gastar sin sufrir estrés. Cuando se agota, hay que regar.

### 4.12 Intervalo y lámina de riego

```
Intervalo (días) = RAW / ETc
Lámina neta (mm) = RAW
Lámina bruta (mm) = RAW / eficiencia del sistema     (gravedad ≈ 0,5–0,6; aspersión ≈ 0,75; goteo ≈ 0,9)
Volumen (m³/ha) = lámina (mm) · 10
```

**Ejemplo con el suelo franco de 4.9 y ETc = 5 mm/día (sin piedras):**

| Cultivo | Zr (m) | p | TAW (mm) | RAW (mm) | Regar cada | Volumen neto por riego |
|---|---|---|---|---|---|---|
| Maíz | 1,0 | 0,55 | 143 | 78 | ~16 días | 780 m³/ha |
| Soya | 0,9 | 0,50 | 128 | 64 | ~13 días | 640 m³/ha |
| Fríjol | 0,7 | 0,45 | 100 | 45 | ~9 días | 450 m³/ha |

Con un 10 % de piedras, el TAW del fríjol baja de 100 a 90 mm. **Esta tabla es la evidencia de que la rotación cambia la estrategia de agua:** mismo lote, misma lluvia, distinto manejo.

### 4.13 Agotamiento inicial a partir de SMAP

```
Dr,0 = 1000 · (θ33 − θ_SMAP) · Zr          acotado entre 0 y TAW
```

**Para qué sirve:** arrancar el balance hídrico con el estado real de la tierra hoy, no con un supuesto.

**Ejemplo:** θ33 = 0,28, SMAP zona radicular = 0,20, fríjol Zr = 0,7 → Dr,0 = 56 mm. Como 56 > RAW (45 mm), **hay que regar ya**.

### 4.14 Balance hídrico diario

```
Dr,i = Dr,i−1 − Pe,i − I_i + ETc,i          acotado entre 0 y TAW
Regar cuando Dr,i ≥ RAW
```

| Variable | Significado |
|---|---|
| Dr,i | Agua que le falta al suelo el día i (mm) |
| Pe,i | Lluvia efectiva del día (IMERG o POWER) |
| I_i | Riego aplicado |
| ETc,i | Consumo del cultivo |

**Para qué sirve:** es el motor del módulo de riego y del seguimiento. Simplificamos escorrentía y ascenso capilar, como permite FAO-56 en suelos sin nivel freático cercano.

### 4.15 Coeficiente de estrés hídrico (Ks)

```
Ks = 1                                       si Dr ≤ RAW
Ks = (TAW − Dr) / ((1 − p) · TAW)            si Dr > RAW
```

**Para qué sirve:** cuantificar cuánto se está afectando el cultivo. Un Ks = 1 significa que no hay estrés; un Ks = 0 significa marchitez.

**Ejemplo:** fríjol con TAW = 100, p = 0,45 y Dr = 70 → Ks = 30 / 55 = **0,55**: el cultivo transpira poco más de la mitad de lo normal.

### 4.16 NDVI y desviación de vigor

```
NDVI = (NIR − Rojo) / (NIR + Rojo)
Desviación = (NDVI_real − NDVI_esperado) / NDVI_esperado
Alerta si Desviación < −15 % en dos observaciones seguidas y (Ks < 1 o LST alta)
```

**Para qué sirve:** detectar desde el satélite que el cultivo va peor de lo esperado para su etapa, y cruzarlo con el balance hídrico para explicar la causa.

---

## 5. Cuantificación del impacto en el agua (ejemplo ilustrativo)

Para dimensionar el impacto que podemos mostrar, comparamos dos formas de regar un ciclo de maíz de 120 días en el suelo franco del ejemplo. **Los supuestos son ilustrativos** y se reemplazarán por datos reales del lote demo.

| Supuesto | Valor |
|---|---|
| ET0 media | 4,7 mm/día |
| Kc medio del ciclo | 0,85 |
| Lluvia | 75 mm/mes → 66 mm/mes efectivos |
| Eficiencia de riego por gravedad | 0,70 |
| Práctica actual supuesta | 40 mm cada 7 días, por calendario |

| Cálculo | Riego por calendario | Riego por balance hídrico (SURCO) |
|---|---|---|
| Demanda del cultivo (ETc) | — | 0,85 × 4,7 × 120 = 479 mm |
| Lluvia efectiva | No se descuenta | 4 × 66 = 264 mm |
| Necesidad neta | — | 479 − 264 = 215 mm |
| Lámina aplicada | 17 riegos × 40 = 680 mm | 215 / 0,70 = 306 mm |
| Diferencia | | **374 mm ≈ 3.740 m³/ha por ciclo (−55 %)** |

El ahorro real dependerá de la práctica de cada productor, del sistema de riego y de la lluvia de la temporada. Lo valioso para el pitch es que el número sale de fórmulas citadas y datos NASA del lote, no de una suposición.

---

## 6. Conjunto mínimo de datos para el MVP

| # | Dato | Fuente | Decisión que mueve |
|---|---|---|---|
| 1 | Temperatura | NASA POWER | Qué sembrar, cuándo se cosecha |
| 2 | Lluvia | NASA POWER + GPM IMERG | Cuánto regar, riesgo en secano |
| 3 | Evapotranspiración | Calculada con POWER (FAO-56) | Cuánta agua pide el cultivo |
| 4 | Humedad del suelo | SMAP L4 | Cuándo regar hoy |
| 5 | Agua que guarda el suelo | SoilGrids + raíz FAO-56 | Cada cuánto regar cada cultivo |
| 6 | Vigor del lote | MODIS / HLS | Seguimiento y alertas |

Cuatro de los seis son datos NASA o se calculan con datos NASA, lo que asegura el criterio de *Relevance*.

---

## 7. Guía para convertir los datos en recomendaciones para el campesino

### 7.1 La cadena

Cada recomendación recorre la misma cadena: **dato → indicador → decisión → mensaje**.

| Dato | Indicador | Decisión | Mensaje |
|---|---|---|---|
| SMAP + SoilGrids + raíz | Agua fácilmente aprovechable | Cada cuánto y cuánto regar | "Riegue cada 9 días" |
| POWER + ensamble ENSO | Probabilidad de completar el ciclo | Qué sembrar y cuándo | "8 de cada 10 años le va bien si siembra antes del 22 de marzo" |
| Familias + nitrógeno | Balance de nitrógeno | Orden de la rotación | "Después del arroz, siembre soya: le deja abono al próximo cultivo" |
| NDVI real vs. esperado | Desviación de vigor | Alerta | "Su lote está más pálido de lo normal para esta etapa" |

### 7.2 Reglas de comunicación

1. **Una decisión por mensaje**, con verbo de acción: siembre, riegue, espere, cambie.
2. **Sin jerga técnica.** "Verdor del lote" en lugar de NDVI; "agua que pierde el cultivo" en lugar de ET0; "humedad de la tierra" en lugar de m³/m³.
3. **Unidades que se entiendan.** 45 mm equivalen a 450 m³ por hectárea; cuando sea posible se traduce a horas de bomba o a tanques.
4. **Probabilidades como frecuencias.** "8 de cada 10 años" en lugar de "P = 0,78".
5. **Un solo "por qué"**: el dato que más pesó, con opción de ver el detalle técnico.

### 7.3 Ejemplo en dos capas

**Capa técnica (para el juez y el técnico agropecuario):**
Fríjol, suelo franco, TAW = 100 mm, RAW = 45 mm, ETc = 5,4 mm/día, SMAP zona radicular = 0,20 m³/m³, agotamiento inicial = 56 mm > RAW.

**Capa del campesino:**
"Riegue su fríjol esta semana y luego cada 8 a 9 días, con unos 450 m³ por hectárea. Su tierra guarda agua para poco más de una semana porque la raíz del fríjol es corta, y hoy ya está seca."

La capa técnica sostiene *Validity* y *Relevance*; la del campesino sostiene *Impact* y *Presentation*. La demo debe mostrar las dos.

---

## 8. Próximos pasos

| Prioridad | Tarea | Responsable sugerido |
|---|---|---|
| 1 | Ajustar la consulta de POWER a las seis variables de la sección 3.2 | Datos satelitales |
| 2 | Script de SoilGrids: propiedades de la sección 3.7 hasta 100 cm, con percentiles y conversión de unidades | Datos satelitales |
| 3 | Agregar Zr y p al catálogo de cultivos | Motor agronómico |
| 4 | Implementar las fórmulas 4.9 a 4.15 con pruebas unitarias usando los ejemplos de este informe | Motor agronómico |
| 5 | Extraer SMAP e IMERG por polígono en Earth Engine | Datos satelitales |
| 6 | Reemplazar los supuestos de la sección 5 con datos del lote demo | Motor + presentación |

---

## 9. Referencias

- Allen, R. G., Pereira, L. S., Raes, D. y Smith, M. (1998). *Crop evapotranspiration: Guidelines for computing crop water requirements*. FAO Irrigation and Drainage Paper 56.
- Saxton, K. E. y Rawls, W. J. (2006). Soil water characteristic estimates by texture and organic matter for hydrologic solutions. *Soil Science Society of America Journal*, 70(5), 1569–1578.
- ISRIC — World Soil Information. SoilGrids 2.0, documentación y preguntas frecuentes (docs.isric.org).
- NASA Langley Research Center. POWER Project, documentación de la API (power.larc.nasa.gov).
- NASA GSFC. SMAP Level 4 Surface and Root Zone Soil Moisture.
- NASA GSFC. GPM IMERG.
- NASA LP DAAC. MODIS MOD13Q1 y Harmonized Landsat Sentinel-2 (HLS).
- USDA Soil Conservation Service. Método de precipitación efectiva (según su implementación en FAO CROPWAT).
