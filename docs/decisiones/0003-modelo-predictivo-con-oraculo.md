# 0003: Modelo predictivo entrenado con un oráculo agronómico

- Estado: aceptada
- Fecha: 2026-10-17
- Complementa: [0001](0001-motor-mcda-explicable.md)

## Contexto
La ADR 0001 dejó el ML para "si hay datos para entrenarlo", porque no existe un dataset etiquetado de "este cultivo fue bueno en este lote" para el Huila. Además, el motor MCDA solo puede evaluar los trapecios del catálogo con el clima que ya pasó, pero el día de la siembra no se sabe qué clima hará durante los 100 a 180 días del ciclo.

## Decisión
- Las etiquetas salen de un **oráculo agronómico**: los trapecios de `surco_agro` y el balance hídrico FAO-56, aplicados al clima real de 1981–2025 en ~600 puntos de Colombia.
- El modelo aprende a predecir esas etiquetas **solo con lo que se sabe el día de la siembra**: el clima previo, SMAP, ENSO, la climatología, el suelo y el sitio.
- Primero un **XGBoost en GPU** explicado con SHAP. Una red de secuencias (SurcoNet) solo si mejora al XGBoost.
- Los filtros duros y el MCDA siguen siendo el núcleo: el modelo alimenta los componentes del índice que dependen del clima.
- El modelo **solo se adopta si le gana a la línea base de climatología** en los años de prueba 2019–2024.

Detalle completo en [ml/README.md](../../ml/README.md).

## Consecuencias
- Hay datos de entrenamiento abundantes sin etiquetar a mano.
- Las etiquetas heredan los umbrales del catálogo, que todavía no están validados. Por eso se calibra con rendimientos reales (EVA, GDHY).
- Necesita una máquina con GPU y una descarga masiva de datos: ver la [guía](../../ml/GUIA_MAQUINA_GPU.md).
