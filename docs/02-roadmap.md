# Roadmap

Se trabaja por fases pequeñas. Cada casilla puede convertirse en un issue de GitHub.

## Fase 0: Base y datos (ahora)
- [x] Estructura del repositorio
- [x] Verificar qué fuentes responden y su cobertura en el Huila → [datos/inventario.md](datos/inventario.md)
- [x] Descargador de series de NASA POWER con corrección de temperatura por elevación
- [ ] Cuentas: Earthdata, Google Earth Engine (cada integrante)
- [ ] Probar `earthaccess` / GEE / AppEEARS con SMAP L4 y MODIS NDVI
- [ ] Elevación real de las fincas demo con un DEM
- [ ] Series 2015–2024 por finca: POWER + SMAP raíz + NDVI + LST + IMERG
- [ ] Validar la corrección de POWER contra MODIS LST o IDEAM

## Fase 1: Investigación agronómica
- [ ] Tabla de cultivos candidatos del Huila con sus requisitos (ver [investigacion/](investigacion/README.md))
- [ ] Reglas de rotación: familias botánicas, intervalos y aporte de N de las leguminosas
- [ ] Umbrales de estrés hídrico y térmico por cultivo
- [ ] Datos de impacto: área y producción del Huila (Agronet/EVA), eventos de El Niño

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
