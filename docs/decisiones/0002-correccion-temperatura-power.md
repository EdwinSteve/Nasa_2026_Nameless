# 0002: Corregir la temperatura de NASA POWER por elevación

- Estado: aceptada (pendiente de validar)
- Fecha: 2026-09-30

## Contexto
Las celdas de POWER (~50 km) en el Huila tienen una elevación media de 1400–2100 m, mientras que las zonas agrícolas del valle están a 430–550 m. Sin corregir, la temperatura sale ~6–7 °C más baja ([inventario](../datos/inventario.md#1-power-subestima-la-temperatura-del-valle-en-7-c)).

## Decisión
Aplicar el gradiente térmico estándar (−6.5 °C/km) a T2M, T2M_MAX y T2M_MIN usando la diferencia entre la elevación de la celda y la del punto. Se guardan las columnas `*_corr` junto a las originales.

## Consecuencias
- Los GDD y los filtros de temperatura salen realistas.
- Hay que validar contra MODIS LST o IDEAM, y obtener la elevación del punto desde un DEM.
