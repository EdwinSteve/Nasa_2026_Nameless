"""Procesa la respuesta de SoilGrids: unidades convencionales y promedios por profundidad.

Diferencia con el esquema 1.0: los valores ya salen convertidos (no en las
unidades 'mapped' de SoilGrids), así que no hay que volver a dividir por d_factor.
"""

# Unidades que no se toman de target_units: el agua retenida se pasa a m³/m³
# para compararla directo con SMAP y con Saxton & Rawls.
UNIDADES_PROPIAS = {
    'wv0010': (1000, 'm3/m3'),
    'wv0033': (1000, 'm3/m3'),
    'wv1500': (1000, 'm3/m3'),
}
TRAMOS_RESUMEN_CM = (30, 60, 100, 200)
FACTOR_SOC_A_MO = 1.724  # hipótesis de van Bemmelen, la misma de normalizer.py


def _convertir(valor, divisor):
    return None if valor is None else round(valor / divisor, 4)


def capas(crudo: dict) -> tuple[dict, dict]:
    """{'0-5cm': {'top_cm': 0, 'bottom_cm': 5, 'properties': {'clay': {'mean': 29.2, ...}}}}, unidades."""
    salida, unidades = {}, {}
    for capa in crudo['properties']['layers']:
        medida = capa['unit_measure']
        divisor, unidad = UNIDADES_PROPIAS.get(capa['name'], (medida.get('d_factor') or 1, medida.get('target_units')))
        unidades[capa['name']] = unidad
        for profundidad in capa['depths']:
            registro = salida.setdefault(profundidad['label'], {
                'top_cm': profundidad['range']['top_depth'],
                'bottom_cm': profundidad['range']['bottom_depth'],
                'properties': {},
            })
            registro['properties'][capa['name']] = {
                estadistica: _convertir(v, divisor) for estadistica, v in profundidad['values'].items()
            }
    return dict(sorted(salida.items(), key=lambda kv: kv[1]['top_cm'])), unidades


def promedio_hasta(capas_suelo: dict, propiedad: str, hasta_cm: float, estadistica: str = 'mean') -> float | None:
    """Promedio ponderado por espesor desde la superficie hasta hasta_cm (informe 08, 4.7).

    Sirve para llevar el suelo a la profundidad de raíz de cada cultivo (Zr del catálogo).
    """
    suma = peso = 0.0
    for capa in capas_suelo.values():
        espesor = max(0.0, min(capa['bottom_cm'], hasta_cm) - capa['top_cm'])
        valor = capa['properties'].get(propiedad, {}).get(estadistica)
        if espesor and valor is not None:
            suma += valor * espesor
            peso += espesor
    return round(suma / peso, 4) if peso else None


def resumen(capas_suelo: dict) -> dict:
    """Promedios 0-30, 0-60, 0-100 y 0-200 cm con media, mediana e incertidumbre relativa."""
    propiedades = sorted({p for c in capas_suelo.values() for p in c['properties']})
    salida = {}
    for hasta in TRAMOS_RESUMEN_CM:
        tramo = {}
        for p in propiedades:
            media = promedio_hasta(capas_suelo, p, hasta, 'mean')
            mediana = promedio_hasta(capas_suelo, p, hasta, 'Q0.5')
            q05 = promedio_hasta(capas_suelo, p, hasta, 'Q0.05')
            q95 = promedio_hasta(capas_suelo, p, hasta, 'Q0.95')
            tramo[p] = {
                'mean': media,
                'Q0.5': mediana,
                # Ancho del intervalo 90 % relativo a la mediana: cuánto confiar en el dato
                'rel_uncertainty': round((q95 - q05) / mediana, 3) if None not in (q05, q95) and mediana else None,
            }
        soc = tramo.get('soc', {}).get('mean')
        tramo['organic_matter_pct'] = None if soc is None else round(soc / 10 * FACTOR_SOC_A_MO, 3)
        salida[f'0-{hasta}cm'] = tramo
    return salida


def control_textura(capas_suelo: dict) -> dict:
    """Suma de arena + limo + arcilla con la media de cada capa (debe dar ~100 %).

    Sumar cuantiles (como hacía el esquema 1.0 con Q0.05 y Q0.95) no tiene sentido físico.
    """
    salida = {}
    for etiqueta, capa in capas_suelo.items():
        valores = [capa['properties'].get(p, {}).get('mean') for p in ('sand', 'silt', 'clay')]
        salida[etiqueta] = None if None in valores else round(sum(valores), 1)
    return salida


def procesar(crudo: dict) -> dict:
    capas_suelo, unidades = capas(crudo)
    vacio = all(
        v is None for c in capas_suelo.values() for est in c['properties'].values() for v in est.values()
    )
    return {
        'units': unidades,
        'empty': vacio,
        'layers': capas_suelo,
        'summary': resumen(capas_suelo),
        'texture_sum_pct': control_textura(capas_suelo),
    }
