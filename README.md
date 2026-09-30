# Nasa_2026_Nameless: Field Shift 🌱🛰️

Proyecto del equipo **Nameless** para el **NASA Space Apps Challenge 2026**, reto **"Field Shift: Adapting Farms with NASA Data"**.

Construimos un **sistema de soporte a la decisión** que, dada una finca del Huila (Colombia), recomienda una **rotación de cultivos resiliente al clima** para 2–3 temporadas, usando datos de observación de la Tierra de la NASA, y explica **qué dato satelital motivó cada decisión**.

## Estado

🟡 **Fase 0: base y datos.** Ver el [roadmap](docs/02-roadmap.md).

## Documentación

| Documento | Contenido |
|---|---|
| [docs/00-reto.md](docs/00-reto.md) | El reto, sus entregables y los criterios |
| [docs/01-estrategia.md](docs/01-estrategia.md) | Estrategia completa: cómo ganar, ideas, arquitectura |
| [docs/02-roadmap.md](docs/02-roadmap.md) | Fases y tareas |
| [docs/datos/inventario.md](docs/datos/inventario.md) | **Datos disponibles y verificados, y sus limitaciones** |
| [docs/investigacion/](docs/investigacion/README.md) | Preguntas abiertas y notas de investigación |
| [docs/decisiones/](docs/decisiones/) | Registro de decisiones técnicas (ADR) |

## Estructura

```
docs/        estrategia, datos, investigación, decisiones
data/        fincas demo + datos procesados (raw/ no se versiona)
scripts/     verificación y descarga de datos
notebooks/   exploración
backend/     FastAPI: motor de rotación (pendiente)
frontend/    Next.js: mapa, planificador, simulador (pendiente)
```

## Inicio rápido

```bash
git clone git@github.com:EdwinSteve/Nasa_2026_Nameless.git
cd Nasa_2026_Nameless
python3 scripts/verificar_fuentes.py         # ¿responden las fuentes de datos?
python3 scripts/descargar_power.py           # series diarias 2015-2024 de las fincas demo
```

Los scripts actuales solo usan la biblioteca estándar de Python 3. Para Earthdata o GEE: `pip install -r scripts/requirements.txt` y copiar `.env.example` a `.env`.

## Cómo trabajamos

- `main` siempre funciona. Cada tarea va en una rama (`datos/smap-fincas`, `docs/cultivos-huila`, `feat/motor-mcda`) y entra por Pull Request.
- Cada tarea del roadmap se convierte en un issue.
- La investigación se escribe en `docs/investigacion/` citando fuentes.
- Las decisiones importantes van en `docs/decisiones/NNNN-titulo.md`.

## Datos NASA utilizados

NASA POWER · SMAP (L3/L4) · GPM IMERG · MODIS (NDVI, LST, ET) · HLS (Landsat/Sentinel-2) · ECOSTRESS · GRACE-FO. Complemento de suelo: SoilGrids (ISRIC). Estado y limitaciones de cada uno en el [inventario](docs/datos/inventario.md).

## Licencia

[MIT](LICENSE)
