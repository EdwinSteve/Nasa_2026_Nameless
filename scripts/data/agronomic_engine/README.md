# Agronomic Engine

Implementación de los apartados 4.9 a 4.15 del modelo agronómico.

## Estructura

```text
agronomic_engine/
├── crops.py
├── engine.py
├── formulas.py
├── normalizer.py
├── validators.py
```

## Cobertura

- 4.9: Saxton & Rawls: θ1500 y θ33.
- 4.10: TAW con corrección por CFVO.
- 4.11: RAW.
- 4.12: intervalo, lámina neta, lámina bruta y volumen.
- 4.13: agotamiento inicial usando humedad SMAP.
- 4.14: balance hídrico diario y decisión de riego.
- 4.15: coeficiente de estrés Ks.

## Responsabilidades

`formulas.py` contiene únicamente cálculos matemáticos.

`crops.py` contiene los parámetros del cultivo (`Zr` y `p`).

`normalizer.py` convierte los valores de SoilGrids a las unidades utilizadas
por el modelo.

`engine.py` orquesta las fórmulas y devuelve el resultado del modelo.

`validations.py` concentra las validaciones de entrada.

## Datos externos

El motor no consulta directamente NASA POWER, SoilGrids o SMAP.

Los servicios externos deben entregar datos normalizados al motor:

```text
NASA POWER / SMAP / SoilGrids
            ↓
       normalización
            ↓
     agronomic_engine
            ↓
      resultado de riego
```

`ETc` debe llegar calculado desde la capa correspondiente de evapotranspiración.
`theta_smap` representa la humedad volumétrica utilizada para inicializar el
agotamiento de la zona radicular.

## SoilGrids y materia orgánica

SoilGrids proporciona `soc` (carbono orgánico del suelo), no `MO` directamente.
La implementación incluye una aproximación explícita:

```text
MO ≈ SOC × 1.724
```

Esta conversión debe considerarse una hipótesis del modelo y puede reemplazarse
por materia orgánica de laboratorio cuando esté disponible.