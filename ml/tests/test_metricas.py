import numpy as np
import pytest

from surco_ml.evaluacion import metricas


def test_pinball_y_cobertura():
    y = np.array([0.0, 1.0, 2.0, 3.0])
    assert metricas.pinball(y, np.full(4, 1.5), 0.5) == pytest.approx(0.5)
    assert metricas.cobertura(y, np.full(4, 0.5), np.full(4, 2.5)) == pytest.approx(0.5)


def test_ece_cero_si_esta_calibrado():
    prob = np.repeat([0.2, 0.8], 10)
    y = np.r_[np.repeat([1, 0], [2, 8]), np.repeat([1, 0], [8, 2])].astype(float)
    assert metricas.ece(y, prob) == pytest.approx(0.0)
    assert metricas.brier(y, prob) == pytest.approx(0.16)


def test_ndcg_perfecto_y_al_reves():
    rel = np.array([0.9, 0.5, 0.1, 0.0, 0.8, 0.2, 0.3, 0.1])
    grupo = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    assert metricas.ndcg_at_k(rel, rel, grupo) == pytest.approx(1.0)
    assert metricas.ndcg_at_k(rel, -rel, grupo) < 0.5
