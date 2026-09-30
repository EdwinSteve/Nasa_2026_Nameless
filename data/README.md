# Datos

| Carpeta/archivo | Contenido | ¿En git? |
|---|---|---|
| `fincas_demo.json` | Puntos de muestra del Huila (coordenadas, elevación, cultivo actual) | Sí |
| `raw/` | Descargas crudas (POWER, SMAP, MODIS...). Se regeneran con los scripts | **No** |
| `processed/` | Resultados pequeños y derivados (reportes de verificación, tablas finales para la demo) | Sí, si pesan < 5 MB |

Regenerar: `python scripts/descargar_power.py`. Más detalle en [docs/datos/inventario.md](../docs/datos/inventario.md).
