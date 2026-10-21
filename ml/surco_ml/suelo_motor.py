"""Agua del suelo a la raíz de cada cultivo con las fórmulas del motor agronómico (4.9 y 4.10).

Reutiliza scripts/data/agronomic_engine para no tener dos versiones de Saxton & Rawls.
"""
import sys

import numpy as np

from .rutas import MOTOR_AGRONOMICO

if str(MOTOR_AGRONOMICO) not in sys.path:
    sys.path.insert(0, str(MOTOR_AGRONOMICO))

from formulas import calculate_taw, calculate_theta_33, calculate_theta_1500  # noqa: E402
from normalizer import weighted_to_depth, soc_to_organic_matter  # noqa: E402


def agua_a_la_raiz(suelo: dict | None, zr_m: float) -> tuple[float, float, float]:
    """(TAW mm, θ33, θ1500) con el suelo promediado hasta Zr. NaN si falta el suelo o Zr."""
    if suelo is None or not np.isfinite(zr_m):
        return np.nan, np.nan, np.nan
    capas = suelo['layers']
    valores = {p: weighted_to_depth(capas, p, zr_m) for p in ('sand', 'clay', 'soc', 'cfvo')}
    if any(v is None for v in valores.values()):
        return np.nan, np.nan, np.nan
    arena, arcilla = valores['sand'] / 100, valores['clay'] / 100
    mo = min(soc_to_organic_matter(valores['soc']), 100.0)
    t33 = calculate_theta_33(sand=arena, clay=arcilla, organic_matter=mo)
    t1500 = calculate_theta_1500(sand=arena, clay=arcilla, organic_matter=mo)
    if t33 < t1500:
        return np.nan, t33, t1500
    taw = calculate_taw(theta_33=t33, theta_1500=t1500, zr=zr_m, cfvo=min(valores['cfvo'], 100.0))
    return taw, t33, t1500
