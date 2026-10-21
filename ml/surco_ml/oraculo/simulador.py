"""Simulador del oráculo: un punto, muchas fechas de siembra y todos los cultivos a la vez.

Para cada fecha de siembra y cultivo:
1. Corta la serie en fases según `duracion_dias` del catálogo (punto medio del rango).
2. Puntúa cada fase con las mismas reglas de data/catalogo_cultivos_mongodb/scripts/ejemplo_modelo.py:
   trapecio de temperatura media, trapecio de lluvia acumulada (secano), rango de humedad
   relativa, días sobre el viento tolerable y días sobre la temperatura crítica.
   Puntaje de la fase = 0,5 · mínimo de los componentes + 0,5 · su media.
   En los cultivos con riego (catalogo.CON_RIEGO) el agua está asegurada: lluvia = 1.
3. Corre el balance hídrico diario (motor agronómico, 4.14 y 4.15) dos veces: en secano para
   contar los días con Ks < 1, y con riego automático cuando Dr supera RAW para la lámina neta.

Etiquetas por cultivo:
- puntaje: 0,5 · peor fase + 0,5 · media de las fases ponderada por `fraccion_del_ciclo`.
- exito: 1 si ninguna fase queda por debajo de UMBRAL_FALLA (falla crítica).
- riego_mm, dias_estres: NaN si el cultivo no tiene Kc y p o el punto no tiene suelo.
- dias_calor: días con Tmax sobre `temp_max_critica_C` en las fases que la tienen.
- fase_critica: índice de la peor fase (para la explicación).

Perennes y semiperennes usan la misma lógica: la "siembra" es el inicio de la ventana anual.
"""
import numpy as np
from numba import njit, prange

from ..catalogo import Cultivos

UMBRAL_FALLA = 0.4         # una fase por debajo de esto es una falla crítica del ciclo
MARGEN_HR = 20.0           # ejemplo_modelo.rango: 0 a 20 puntos de HR fuera del óptimo
DIAS_CALOR_CERO = 5.0      # 5 o más días sobre la temperatura crítica = componente en 0
DIAS_ARRANQUE = 60         # días antes de la siembra para estabilizar el agotamiento inicial
AGOTAMIENTO_ARRANQUE = 0.5  # fracción de TAW al comenzar el arranque

ETIQUETAS = ('puntaje', 'exito', 'riego_mm', 'dias_estres', 'dias_calor', 'fase_critica')


@njit(cache=True)
def trapecio(x, a, b, c, d):
    """Pertenencia 0-1 a un trapecio (igual que ejemplo_modelo.trapecio)."""
    if x <= a or x >= d:
        return 0.0
    if b <= x <= c:
        return 1.0
    if x < b:
        return (x - a) / (b - a) if b > a else 1.0
    return (d - x) / (d - c) if d > c else 1.0


@njit(cache=True)
def rango(x, lo, hi, margen):
    """1 dentro del óptimo; cae linealmente a 0 a `margen` unidades (igual que ejemplo_modelo.rango)."""
    if lo <= x <= hi:
        return 1.0
    dist = lo - x if x < lo else x - hi
    return max(0.0, 1.0 - dist / margen)


@njit(cache=True)
def puntaje_fase(t, tmax, lluvia, hr, viento, i0, i1, temp, llu, hro, vmax, tcrit, con_riego=False):
    """Puntaje de una fase con los días [i0, i1). Devuelve (puntaje, días sobre la temperatura crítica).

    con_riego: el agua está asegurada (componente de lluvia = 1); su costo va en riego_mm.
    """
    n = i1 - i0
    t_media = 0.0
    lluvia_total = 0.0
    hr_media = 0.0
    dias_viento = 0
    dias_calor = 0
    for i in range(i0, i1):
        t_media += t[i]
        lluvia_total += lluvia[i]
        hr_media += hr[i]
        if viento[i] > vmax:
            dias_viento += 1
        if tmax[i] > tcrit:  # NaN nunca supera: fases sin temperatura crítica dan 0
            dias_calor += 1
    t_media /= n
    hr_media /= n

    comp = np.empty(5)
    k = 0
    comp[k] = trapecio(t_media, temp[0], temp[1], temp[2], temp[3]); k += 1
    comp[k] = 1.0 if con_riego else trapecio(lluvia_total, llu[0], llu[1], llu[2], llu[3]); k += 1
    if np.isfinite(hro[0]) and np.isfinite(hro[1]):
        comp[k] = rango(hr_media, hro[0], hro[1], MARGEN_HR); k += 1
    if np.isfinite(vmax):
        comp[k] = 1.0 - dias_viento / n; k += 1
    if np.isfinite(tcrit):
        comp[k] = max(0.0, 1.0 - dias_calor / DIAS_CALOR_CERO); k += 1
    minimo = comp[0]
    suma = 0.0
    for j in range(k):
        minimo = min(minimo, comp[j])
        suma += comp[j]
    return 0.5 * minimo + 0.5 * suma / k, dias_calor


@njit(parallel=True, cache=True)
def _simular(t, tmax, lluvia, hr, viento, et0, siembras,
             n_fases, duracion, fraccion, kc, p, temp, llu, hro, vmax, tcrit, taw, tiene_agua, con_riego):
    S, C = len(siembras), len(n_fases)
    N = len(t)
    puntaje = np.full((S, C), np.nan)
    exito = np.full((S, C), np.nan)
    riego = np.full((S, C), np.nan)
    estres = np.full((S, C), np.nan)
    calor = np.full((S, C), np.nan)
    critica = np.full((S, C), -1.0)
    for idx in prange(S * C):
        k = idx // C
        c = idx % C
        s = siembras[k]
        nf = n_fases[c]
        total = 0
        for f in range(nf):
            total += duracion[c, f]
        if s < 0 or s + total > N:
            continue

        # --- Fases contra sus trapecios
        peor = 2.0
        f_peor = -1
        ponderado = 0.0
        peso = 0.0
        calor_c = 0
        i0 = s
        for f in range(nf):
            i1 = i0 + duracion[c, f]
            pf, dc = puntaje_fase(t, tmax, lluvia, hr, viento, i0, i1,
                                  temp[c, f], llu[c, f], hro[c, f], vmax[c, f], tcrit[c, f], con_riego[c])
            calor_c += dc
            ponderado += fraccion[c, f] * pf
            peso += fraccion[c, f]
            if pf < peor:
                peor = pf
                f_peor = f
            i0 = i1
        puntaje[k, c] = 0.5 * peor + 0.5 * ponderado / peso
        exito[k, c] = 1.0 if peor >= UMBRAL_FALLA else 0.0
        calor[k, c] = calor_c
        critica[k, c] = f_peor

        # --- Balance hídrico (4.14) y estrés (4.15)
        T = taw[c]
        if not tiene_agua[c] or not np.isfinite(T) or T <= 0:
            continue
        dr = AGOTAMIENTO_ARRANQUE * T
        for i in range(max(0, s - DIAS_ARRANQUE), s):   # arranque con el Kc inicial
            raw = p[c, 0] * T
            ks = 1.0 if dr <= raw else max(0.0, (T - dr) / ((1.0 - p[c, 0]) * T))
            dr = min(max(dr - lluvia[i] + ks * kc[c, 0] * et0[i], 0.0), T)
        dr_riego = dr
        dias_estres = 0
        lamina = 0.0
        i0 = s
        for f in range(nf):
            raw = p[c, f] * T
            for i in range(i0, i0 + duracion[c, f]):
                etc = kc[c, f] * et0[i]
                ks = 1.0 if dr <= raw else max(0.0, (T - dr) / ((1.0 - p[c, f]) * T))
                if ks < 1.0:
                    dias_estres += 1
                dr = min(max(dr - lluvia[i] + ks * etc, 0.0), T)
                dr_riego = min(max(dr_riego - lluvia[i] + etc, 0.0), T)
                if dr_riego > raw:          # riego automático hasta capacidad de campo
                    lamina += dr_riego
                    dr_riego = 0.0
            i0 += duracion[c, f]
        riego[k, c] = lamina
        estres[k, c] = dias_estres
    return puntaje, exito, riego, estres, calor, critica


def simular(v: dict[str, np.ndarray], siembras: np.ndarray, cultivos: Cultivos, taw: np.ndarray) -> dict[str, np.ndarray]:
    """v: arreglos diarios de series.Serie.v (o una serie de climatología con las mismas claves).

    siembras: índices de día dentro de la serie. taw: (C,) agua total disponible por cultivo (mm).
    Devuelve un dict ETIQUETAS -> (S, C).
    """
    salida = _simular(
        v['t'], v['tmax'], v['lluvia'], v['hr'], v['viento'], v['et0'], np.asarray(siembras, np.int64),
        cultivos.n_fases, cultivos.duracion, cultivos.fraccion, cultivos.kc, cultivos.p,
        cultivos.temp, cultivos.lluvia, cultivos.hr, cultivos.viento_max, cultivos.temp_critica,
        np.asarray(taw, np.float64), cultivos.tiene_agua, cultivos.con_riego,
    )
    return dict(zip(ETIQUETAS, salida))
