# Roadmap

Se trabaja por fases pequeñas. Cada casilla puede convertirse en un issue de GitHub.

## Fase 0: Base y datos (ahora)
- [x] Estructura del repositorio
- [x] Verificar qué fuentes responden y su cobertura en el Huila → [datos/inventario.md](datos/inventario.md)
- [x] Descargador de series de NASA POWER con corrección de temperatura por elevación
- [x] Cuentas: Earthdata, Google Earth Engine (cada integrante)
- [x] Probar `earthaccess` / GEE / AppEEARS con SMAP L4 y MODIS NDVI
- [x] Investigacion Dani & Steve, sobre las metricas y datos mas relevantes para el desarrollo del proyecto → [investigacion/08_INFORME_FUENTES_Y_FORMULAS.md](investigacion/08_INFORME_FUENTES_Y_FORMULAS.md)
- [x] Elevación real con un DEM (SRTM 30 m en `ml/datos_tierra`)
- [x] Servicio de datos con POWER + SMAP + IMERG + MODIS + SoilGrids + DEM + ENSO → [ml/datos_tierra](../ml/datos_tierra/README.md)
- [x] Validar la corrección de POWER contra MODIS LST o IDEAM

## Fase 1: Investigación agronómica
- [x] Tabla de cultivos candidatos del Huila con sus requisitos (ver [investigacion/](investigacion/README.md))
- [x] Reglas de rotación: familias botánicas, intervalos y aporte de N de las leguminosas
- [x] Umbrales de estrés hídrico y térmico por cultivo
- [x] Datos de impacto: área y producción del Huila (Agronet/EVA), eventos de El Niño

## Fase 1b: Modelo predictivo de idoneidad → [ml/README.md](../ml/README.md)
- [x] Arquitectura del modelo y estudio de datos ([estudio](datos/estudio-datos-modelo.md))
- [x] Puntos de entrenamiento y descarga masiva 1981–2025 ([guía de la máquina GPU](../ml/GUIA_MAQUINA_GPU.md))
- [x] Oráculo agronómico: trapecios del catálogo + balance hídrico
- [x] Dataset de etiquetas y features sin fuga de información
- [x] Modelo A (XGBoost en GPU) que le gane a la línea base de climatología
- [x] Calibración con rendimientos reales (EVA, GDHY)

## Fase 2: Motor de rotación (MVP)
- [x] `backend/`: FastAPI con endpoint `/fincas/{id}/recomendacion`
- [x] Filtros duros + puntaje MCDA + explicación con los valores NASA usados
- [x] Métricas: agua ahorrada, N fijado, diversidad

## Fase 3: Frontend + simulador
- [x] Mapa con las fincas demo
- [x] Planificador de rotación con su explicación
- [x] Controles de escenario (lluvia y temperatura)

## Fase 4: Asistente en español (RAG)
- [ ] Corpus de documentos agronómicos (AGROSAVIA, FAO)
- [ ] Contexto de la finca inyectado en el prompt

## Fase 5: Presentación
- [ ] Guion del video (desde la fase 1)
- [ ] Página del proyecto, capturas y diagrama
- [ ] Grabar el video y hacer el envío final
