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
- [ ] Validar la corrección de POWER contra MODIS LST o IDEAM

## Fase 1: Investigación agronómica
- [x] Tabla de cultivos candidatos con sus requisitos por fase → [catálogo surco_agro](../data/catalogo_cultivos_mongodb/README.md)
- [ ] Kc, Zr y p medidos para los 7 cultivos sin dato ([ADR 0005](decisiones/0005-valores-por-analogo-en-catalogo.md))
- [ ] Reglas de rotación: familias botánicas, intervalos y aporte de N de las leguminosas
- [ ] Umbrales de estrés hídrico y térmico por cultivo
- [ ] Datos de impacto: área y producción del Huila (Agronet/EVA), eventos de El Niño

## Fase 1b: Modelo predictivo de idoneidad → [ml/README.md](../ml/README.md)
- [x] Arquitectura del modelo y estudio de datos ([estudio](datos/estudio-datos-modelo.md))
- [ ] Puntos de entrenamiento y descarga masiva 1981–2025 ([guía de la máquina GPU](../ml/GUIA_MAQUINA_GPU.md))
- [ ] Oráculo agronómico: trapecios del catálogo + balance hídrico
- [ ] Dataset de etiquetas y features sin fuga de información
- [ ] Modelo A (XGBoost en GPU) que le gane a la línea base de climatología
- [ ] Calibración con rendimientos reales (EVA, GDHY)

## Fase 2: Motor de rotación (MVP)
- [ ] `backend/`: FastAPI con endpoint `/fincas/{id}/recomendacion`
- [ ] Filtros duros + puntaje MCDA + explicación con los valores NASA usados
- [ ] Métricas: agua ahorrada, N fijado, diversidad

## Fase 3: Frontend + simulador
- [ ] Mapa con las fincas demo
- [ ] Planificador de rotación con su explicación
- [ ] Controles de escenario (lluvia y temperatura)

## Fase 4: Asistente en español (RAG)
- [ ] Corpus de documentos agronómicos (AGROSAVIA, FAO)
- [ ] Contexto de la finca inyectado en el prompt

## Fase 5: Presentación
- [ ] Guion del video (desde la fase 1)
- [ ] Página del proyecto, capturas y diagrama
- [ ] Grabar el video y hacer el envío final
