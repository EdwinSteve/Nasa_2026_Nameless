"""Calibración del modelo A con el corte de validación (2015-2018), nunca con el de prueba.

- P(éxito): regresión isotónica. Se guarda como tabla (umbrales x -> y) y se aplica con
  np.interp, así el backend no necesita scikit-learn.
- Intervalos p10/p90: conformal por cuantiles (CQR) asimétrico. En validación se mide cuánto
  hay que abrir cada extremo para que caiga ~10 % de los casos debajo de p10 y ~10 % encima de
  p90, por separado para cada tipo de ciclo (los perennes se equivocan más que los transitorios).
"""
import numpy as np
from sklearn.isotonic import IsotonicRegression

COLA = 0.10                      # fracción objetivo fuera de cada extremo del intervalo p10-p90
TIPOS_CICLO = (0, 1, 2)          # transitorio, semiperenne, perenne (catalogo.TIPOS_CICLO)


def ajustar_isotonica(prob: np.ndarray, y: np.ndarray) -> dict:
    ok = np.isfinite(prob) & np.isfinite(y)
    iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds='clip').fit(prob[ok], y[ok])
    return {'x': iso.X_thresholds_.tolist(), 'y': iso.y_thresholds_.tolist()}


def aplicar_isotonica(prob: np.ndarray, tabla: dict) -> np.ndarray:
    return np.interp(prob, tabla['x'], tabla['y'])


def ajustar_conformal(y: np.ndarray, p10: np.ndarray, p90: np.ndarray, grupo: np.ndarray) -> dict:
    """{tipo_ciclo: (abrir_abajo, abrir_arriba)}. Puede ser negativo si el intervalo ya era ancho."""
    salida = {}
    for g in TIPOS_CICLO:
        m = (grupo == g) & np.isfinite(y) & np.isfinite(p10) & np.isfinite(p90)
        if m.sum() < 100:
            salida[str(g)] = (0.0, 0.0)
            continue
        n = m.sum()
        nivel = min(1.0, (1 - COLA) * (1 + 1 / n))   # corrección de muestra finita de conformal
        abajo = float(np.quantile(p10[m] - y[m], nivel))
        arriba = float(np.quantile(y[m] - p90[m], nivel))
        salida[str(g)] = (abajo, arriba)
    return salida


def aplicar_conformal(p10, p50, p90, grupo, tabla: dict, minimo: float | None = None, maximo: float | None = None):
    abajo = np.array([tabla[str(g)][0] for g in TIPOS_CICLO])[grupo.astype(int)]
    arriba = np.array([tabla[str(g)][1] for g in TIPOS_CICLO])[grupo.astype(int)]
    lo = np.minimum(p10 - abajo, p50)
    hi = np.maximum(p90 + arriba, p50)
    if minimo is not None:
        lo = np.maximum(lo, minimo)
    if maximo is not None:
        hi = np.minimum(hi, maximo)
    return lo, hi
