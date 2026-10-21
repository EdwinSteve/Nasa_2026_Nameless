import numpy as np
import pytest

from surco_ml.modelos import calibracion


def test_isotonica_corrige_una_probabilidad_sesgada():
    rng = np.random.default_rng(7)
    real = rng.uniform(0, 1, 50000)
    y = (rng.uniform(0, 1, 50000) < real).astype(float)
    sesgada = real ** 2                          # el modelo subestima
    tabla = calibracion.ajustar_isotonica(sesgada, y)
    corregida = calibracion.aplicar_isotonica(sesgada, tabla)
    for lo in (0.2, 0.5, 0.8):
        m = (corregida >= lo - 0.05) & (corregida < lo + 0.05)
        assert y[m].mean() == pytest.approx(corregida[m].mean(), abs=0.03)


def test_conformal_deja_diez_por_ciento_en_cada_cola():
    rng = np.random.default_rng(7)
    n = 60000
    grupo = rng.integers(0, 3, n)
    y = rng.normal(0, 1 + grupo, n)              # los grupos se equivocan distinto
    p50 = np.zeros(n)
    p10, p90 = p50 - 0.5, p50 + 0.5              # intervalo demasiado estrecho
    tabla = calibracion.ajustar_conformal(y[:30000], p10[:30000], p90[:30000], grupo[:30000])
    lo, hi = calibracion.aplicar_conformal(p10[30000:], p50[30000:], p90[30000:], grupo[30000:], tabla)
    yt, gt = y[30000:], grupo[30000:]
    for g in range(3):
        m = gt == g
        assert (yt[m] < lo[m]).mean() == pytest.approx(0.10, abs=0.015)
        assert (yt[m] > hi[m]).mean() == pytest.approx(0.10, abs=0.015)


def test_conformal_respeta_los_limites_y_la_mediana():
    tabla = {'0': (0.5, 0.5), '1': (0.0, 0.0), '2': (-0.1, -0.1)}
    lo, hi = calibracion.aplicar_conformal(np.array([0.2, 0.4, 0.45]), np.array([0.3, 0.5, 0.5]),
                                           np.array([0.4, 0.6, 0.55]), np.array([0, 1, 2]), tabla, 0.0, 1.0)
    assert lo[0] == 0.0 and hi[0] == pytest.approx(0.9)
    assert lo[2] <= 0.5 <= hi[2]
