# Bitácora: frontend, servicio de datos y bases del modelo predictivo

> Período: 2026-10-16 a 2026-10-20. Qué se hizo, qué se decidió, qué se encontró y qué queda pendiente.

## 1. Resumen

| Fecha | Qué | Rama / MR | Estado |
|---|---|---|---|
| 10-16 | Frontend: wizard de registro y pantalla de diagnóstico | `feat/frontend-registro-diagnostico` | ⏳ **MR por abrir** (se fusiona con `main` sin conflictos) |
| 10-17 | Arquitectura del modelo predictivo | `feature/datos-tierra` → MR #13 | ✅ En `main` |
| 10-17 | Servicio de datos `datos_tierra` y estudio de datos | MR #13 | ✅ En `main` |
| 10-17 | Catálogo `surco_agro` versionado en el repo | MR #13 | ✅ En `main` |
| 10-17 | Earth Engine configurado en la laptop | (configuración local) | ✅ |
| 10-17 | Guía de la máquina de entrenamiento | MR #13 | ✅ En `main` |
| 10-20 | Catálogo: 5 cultivos completados por análogo | `feature/catalogo-y-documentacion` | ⏳ **MR por abrir** |
| 10-20 | Catálogo cargado en el MongoDB local | (base local) | ✅ |
| 10-20 | Decisiones 0003 a 0005 y esta bitácora | `feature/catalogo-y-documentacion` | ⏳ **MR por abrir** |

## 2. Frontend (Next.js)

Rama `feat/frontend-registro-diagnostico`, un commit ([README del frontend](../../frontend/README.md) en esa rama).

- **`/registro`**: wizard de 4 pasos.
  - Paso 1, tus datos: celular +57, contraseña y política de datos.
  - Paso 2, tu finca: municipio, corregimiento y vereda.
  - Paso 3, marca tu lote: polígono por caminata o coordenadas, área en ha, riego y cultivo anterior.
  - Paso 4, prioridades: ordenar agua, ganancia, suelo y riesgo.
- **`/lotes/:id?tarea=X`**: diagnóstico en curso, con un satélite que escanea el polígono real y avance por capa (clima, humedad, suelo, verdor).
- **Diseño:** pensado para el campo (botones de 56 px, alto contraste), accesible (ARIA, `prefers-reduced-motion`) y con la paleta de SURCO.
- **API:** `src/api/services.ts` todavía devuelve datos de ejemplo. Para conectar FastAPI solo cambia el cuerpo de cada función.

## 3. Modelo predictivo

Documento: [ml/README.md](../../ml/README.md). Decisión: [ADR 0003](../decisiones/0003-modelo-predictivo-con-oraculo.md).

- **Qué predice:** para cada uno de los 44 cultivos, con lo que se sabe el día de la siembra, cómo puntuará con el clima que realmente ocurra. Entrega un puntaje con intervalo, la probabilidad de éxito, los mm de riego y los días de estrés.
- **Etiquetas:** un oráculo agronómico (trapecios del catálogo + balance hídrico) sobre 1981–2025 en ~600 puntos, es decir ~28 M de simulaciones. Después se calibra con rendimientos reales (EVA, GDHY).
- **Modelos:** A es XGBoost en GPU con SHAP y es obligatorio. B es SurcoNet (Transformer), que recibe cada cultivo como su ficha del catálogo, y es opcional.
- **Validación:** entrenar con 1981–2014 y probar con 2019–2024, con el Huila fuera de los datos en una corrida. Tiene que ganarle a la línea base de climatología.
- **Máquina:** RTX 5060 Ti 16 GB (Blackwell), que necesita PyTorch con CUDA 12.8.

## 4. Servicio de datos `ml/datos_tierra`

Documentos: [README del servicio](../../ml/datos_tierra/README.md) y [estudio de datos](../datos/estudio-datos-modelo.md).

Sale de `scripts/data/external_apis/unificated.py` (PR #12), mantiene su formato y pasa a la versión 2.0:

| Se agregó | Para qué |
|---|---|
| POWER de 7 a 18 variables, incluidas `T2M` y el punto de rocío | `T2M` es lo que compara el catálogo |
| Elevación SRTM 30 m + corrección de temperatura (ADR 0002) | Villavieja: +6,6 °C |
| ET0 FAO-56 Penman-Monteith (+ Hargreaves) | Balance hídrico |
| ONI (El Niño / La Niña) | Predictibilidad estacional |
| Climatología 1991–2020 por día del año | Feature del día de la siembra |
| SoilGrids hasta 200 cm convertido, con `wv0033` y `wv1500` | TAW y contraste de Saxton & Rawls |
| MODIS NDVI, LST y cobertura | Vigor, calor y selección de puntos |
| SMAP e IMERG por bloques | Series de décadas |
| Comandos `lote`, `masivo` y `puntos` | Inferencia y entrenamiento con el mismo código |

Se probó en vivo con las 7 fuentes y tiene 17 pruebas unitarias, incluidos los ejemplos de FAO-56.

## 5. Earth Engine

- `GEE_PROJECT` va en `.env`, que no se versiona. El servicio lo carga solo.
- La autenticación es por máquina: `bash ml/autenticar_gee.sh`, o en Windows `python -c "import ee; ee.Authenticate()"`.
- **No usar** el script `setup_adc.sh` de Google: configura Vertex AI y Gemini, activa esa API y no pide el permiso de Earth Engine.

## 6. Catálogo `surco_agro`

- **Versionado** en `data/catalogo_cultivos_mongodb/`: 44 cultivos, 81 variedades, 11 métricas y 7 fuentes.
- **Completado por análogo** ([ADR 0005](../decisiones/0005-valores-por-analogo-en-catalogo.md)):

| Cultivo | Análogo | Confianza |
|---|---|---|
| Arracacha | Zanahoria (Apiaceae) | Media |
| Mora de Castilla | Berries de FAO-56 (*Rubus*) | Media: el Kc inicial es de clima templado |
| Lulo | Berenjena (*Solanum*) | Media |
| Uchuva | Tomate (Solanaceae) | Media |
| Crotalaria | Soya (Fabaceae), solo Zr y p | Media |

  Ñame, mango, guayaba, papaya, maracuyá, granadilla y tomate de árbol siguen sin Kc ni p, a propósito. En la rama del modelo predictivo ya recibieron Zr: medida en estudios publicados para cinco y por analogía de confianza baja para granadilla y tomate de árbol.

- **Cargado en el MongoDB local** (`127.0.0.1:27017`):
  1. Respaldo previo en `data/raw/respaldos/`.
  2. `01_crear_base.js`: la colección no tenía validador ni índices.
  3. `02_cargar_datos.js`.

  Resultado: 44 cultivos (5 actualizados a `version: 2`), 81 variedades, 11 métricas y 7 fuentes, con validador estricto y 0 documentos fuera de esquema.
- **Nota de la laptop:** VS Code corre en Flatpak y no ve el MongoDB del sistema. Desde la terminal del sistema, o con `flatpak-spawn --host mongosh ...`, sí lo ve.

## 7. Hallazgos que conviene recordar

| Hallazgo | Consecuencia |
|---|---|
| POWER en Villavieja: celda a 1403 m, lote a 385 m | Sin corregir, el valle sale ~6,6 °C más frío |
| Temperatura corregida contra MODIS LST (enero de 2024) | De día: 28,0 → 34,7 °C, y MODIS ve 32,1 °C. De noche: 23,8 °C frente a 24,8 °C |
| IMERG da 67 mm en enero de 2024 y POWER 25 mm | Se prioriza IMERG (11 km) sobre POWER (50 km) |
| La radiación de POWER empieza en 1984 | La ET0 de 1981–1983 es Hargreaves |
| `EVPTRNS` de POWER viene en MJ/m²/día | Se convierte a mm (÷ 2,45) |
| Sumar los cuantiles de textura no tiene sentido (daba de 7,7 a 243 %) | Se controla con la media (100 %) |
| SoilGrids tarda de 1 a 10 min por punto | Se pide una vez y se guarda |
| El punto demo de Pitalito cae en el casco urbano | SoilGrids lo devuelve vacío |
| El punto demo de Villavieja es sabana según MODIS | Los puntos de entrenamiento salen del comando `puntos` |
| El ONI de JAS 2026 es +2,16 | Hay un El Niño fuerte en curso |

## 8. Pendientes

| Pendiente | Área |
|---|---|
| Abrir las MR de `feat/frontend-registro-diagnostico` y `feature/catalogo-y-documentacion` | Todos |
| Montar la máquina GPU, generar los puntos y lanzar la descarga masiva ([guía](../../ml/GUIA_MAQUINA_GPU.md)) | Modelo |
| Oráculo, dataset y modelo A | Modelo |
| Ajustar `normalizer.py` al suelo del esquema 2.0, que ya viene convertido | Motor agronómico |
| Recalcular la lluvia por fase de los 5 cultivos completados, repartida por consumo (Kc) | Catálogo |
| Conseguir Kc, Zr y p medidos para los 7 cultivos sin dato | Catálogo / investigación |
| Mover el punto demo de Pitalito a zona rural | Datos |
| Conectar `services.ts` del frontend a FastAPI y el mapa a Leaflet | Frontend |
| Recargar `surco_agro` en cada base local cuando cambien los JSON | Todos |
