"""Métricas de la sección 6 de ml/README.md. Funciones puras de NumPy."""
import numpy as np


def mae(y: np.ndarray, pred: np.ndarray) -> float:
    ok = np.isfinite(y) & np.isfinite(pred)
    return float(np.abs(y[ok] - pred[ok]).mean())


def pinball(y: np.ndarray, pred: np.ndarray, q: float) -> float:
    ok = np.isfinite(y) & np.isfinite(pred)
    d = y[ok] - pred[ok]
    return float(np.maximum(q * d, (q - 1) * d).mean())


def cobertura(y: np.ndarray, p10: np.ndarray, p90: np.ndarray) -> float:
    """Fracción de casos dentro del intervalo p10-p90. Lo honesto es ~0,80."""
    ok = np.isfinite(y) & np.isfinite(p10) & np.isfinite(p90)
    return float(((y[ok] >= p10[ok]) & (y[ok] <= p90[ok])).mean())


def brier(y: np.ndarray, prob: np.ndarray) -> float:
    ok = np.isfinite(y) & np.isfinite(prob)
    return float(((prob[ok] - y[ok]) ** 2).mean())


def ece(y: np.ndarray, prob: np.ndarray, bins: int = 10) -> float:
    """Error de calibración esperado: que "8 de cada 10 años" se cumpla 8 de cada 10 veces."""
    ok = np.isfinite(y) & np.isfinite(prob)
    y, prob = y[ok], prob[ok]
    caja = np.minimum((prob * bins).astype(int), bins - 1)
    total = 0.0
    for b in range(bins):
        m = caja == b
        if m.any():
            total += m.sum() * abs(prob[m].mean() - y[m].mean())
    return float(total / len(y))


def ndcg_at_k(relevancia: np.ndarray, puntaje: np.ndarray, grupo: np.ndarray, k: int = 3) -> float:
    """NDCG@k promedio por grupo (lote-fecha): ¿el top k de cultivos es el correcto?

    relevancia: puntaje real del oráculo; puntaje: lo que ordena (modelo o línea base).
    """
    orden = np.lexsort((-puntaje, grupo))
    g, rel = grupo[orden], relevancia[orden]
    ideal = np.lexsort((-relevancia, grupo))
    rel_ideal = relevancia[ideal]
    cortes = np.flatnonzero(np.r_[True, g[1:] != g[:-1], True])
    descuento = 1 / np.log2(np.arange(2, k + 2))
    valores = []
    for a, b in zip(cortes[:-1], cortes[1:]):
        n = min(k, b - a)
        dcg = (rel[a:a + n] * descuento[:n]).sum()
        idcg = (rel_ideal[a:a + n] * descuento[:n]).sum()
        if idcg > 0:
            valores.append(dcg / idcg)
    return float(np.mean(valores))
