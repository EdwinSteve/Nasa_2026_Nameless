# 0001: Motor de reglas MCDA explicable antes que ML

- Estado: aceptada
- Fecha: 2026-09-22

## Contexto
No tenemos un dataset etiquetado de "rotación buena o mala" para el Huila, y los jueces valoran la validez y la explicabilidad.

## Decisión
El núcleo es un motor de filtros agronómicos duros más un puntaje ponderado (MCDA), que muestra en cada recomendación los valores NASA que la produjeron. Se agrega ML (XGBoost) solo si queda tiempo y hay datos para entrenarlo.

## Consecuencias
- Todo es explicable y se puede defender con fuentes.
- La calidad depende de la investigación agronómica (umbrales) → la fase 1 es crítica.
