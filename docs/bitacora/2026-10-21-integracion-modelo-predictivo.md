# Bitácora: integración del modelo predictivo y de la etapa 1

> 2026-10-21. Rama `feature/etapa1-registro`.

## 1. Ramas fusionadas

| Rama | Qué traía | Conflictos |
|---|---|---|
| `origin/main` | Frontend del registro (PR #11) | Ninguno |
| `origin/feature/modelo-predictivo` | Contiene a `catalogo-raiz-agua`, `normalizer-esquema-2` y `datos-tierra-suelo`: Zr de los 44 cultivos, normalizer 2.0, SoilGrids por Earth Engine, puntos con WorldCover, oráculo, dataset, modelo A en GPU y `predecir.py` | `.gitignore` (se conservaron las dos partes) |
| `feature/catalogo-y-documentacion` | ADR 0003-0005, bitácora del 20 de octubre | `cultivos.json` (se tomó el del modelo predictivo: mismos valores en los 5 cultivos por análogo y además Zr de los otros 7), estudio de datos y `.gitignore` |

Después de fusionar se alinearon la sección 9 del README del catálogo, la ADR 0005 y la bitácora con el catálogo de 44 cultivos.

## 2. Qué se integró en la app

- **Suelo del diagnóstico por Earth Engine** (~2 s, mismos mapas que la API de ISRIC, que queda de respaldo). Ahora también hay suelo en los cascos urbanos, que la API enmascara.
- **Recomendación de cultivos** (`backend/app/modules/recomendacion`): `POST` y `GET /lotes/{id}/recomendaciones` y `GET /recomendaciones/modelo`. Corre `surco_ml.predecir.recomendar()` en segundo plano sobre el punto medio del lote.
- **Ficha del lote provisional** en la UI con "¿Qué me conviene sembrar?".
- **Docker**: la imagen incluye `surco_ml`, el catálogo, los modelos y las fórmulas del motor.

## 3. Error de datos encontrado y corregido

**POWER infla la lluvia ~24 veces en toda la respuesta si la consulta incluye las últimas ~3 semanas.** En Fortalecillas, 2024 daba 1255 mm si la consulta terminaba en 2025 y 30 121 mm si terminaba el 2026-10-01. Afectaba la predicción (la climatología de lluvia de 210 días salía en 22 784 mm en lugar de 949 mm). **El entrenamiento no estaba afectado**: usa años completos hasta 2025. Corrección en `datos_tierra/fuentes/power.py`: la historia se pide hasta hace 45 días y el tramo reciente aparte; si su lluvia es imposible se descarta y ahí se usa IMERG.

## 4. Cómo se verificó

- Pruebas: backend 168 + 15 de integración contra PostgreSQL; `ml` 46; motor agronómico 27; frontend compila sin errores de tipos ni de lint.
- De punta a punta en un navegador de celular: registro → diagnóstico (4 de 4 pasos con datos reales en 10 s) → ficha → recomendación (31 s) con **modelos de prueba** que tienen las 131 features reales. Los modelos de prueba se borraron.
- La imagen de Docker se construyó con podman.

## 5. Pendientes

| Pendiente | Quién |
|---|---|
| Copiar los `modelo_a_*.ubj` de la máquina de entrenamiento al servidor del backend y probar la recomendación real | Modelo |
| Revisar los dos cultivos con Zr por analogía de confianza baja (granadilla, tomate de árbol) | Catálogo |
| Diseñar la ficha del lote final en Stitch (la actual es provisional) | Frontend |
| Mensaje claro en la UI cuando un paso del diagnóstico falla | Frontend / backend |
| Revisar los términos de uso de las imágenes de Esri del mapa | Equipo |
