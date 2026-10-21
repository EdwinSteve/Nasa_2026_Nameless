"""Etiquetas del oráculo para un punto: clima real y línea base de climatología.

- Etiquetas reales: el simulador con el clima que ocurrió en cada ciclo.
- Línea base (`*_clim`): el mismo simulador con la climatología diaria del punto calculada SIN
  el año de la siembra ni el siguiente (los ciclos largos llegan al año siguiente). Es lo que
  haría un MCDA sin modelo; el modelo A tiene que ganarle.
- `exito_frec_clim`: frecuencia de éxito de esa fecha y cultivo en los DEMÁS años, la línea
  base honesta para P(éxito) ("8 de cada 10 años").
"""
from datetime import date

import numpy as np

from ..catalogo import Cultivos
from ..rutas import ANIOS, DIAS_SIEMBRA
from ..series import Serie
from ..suelo_motor import agua_a_la_raiz
from . import simulador

VARIABLES_ORACULO = ('t', 'tmax', 'lluvia', 'hr', 'viento', 'et0')
VENTANA_CLIMA = 15          # días, igual que datos_tierra.derivadas.climatologia_diaria
ANIOS_SERIE_CLIMA = 3       # la piña dura ~525 días: una siembra en diciembre llega al tercer año


def fechas_siembra(serie: Serie) -> dict[str, np.ndarray]:
    """24 fechas por año (el 1 y el 16 de cada mes) dentro de ANIOS y de la serie."""
    filas = []
    for anio in range(ANIOS[0], ANIOS[1] + 1):
        for mes in range(1, 13):
            for dia in DIAS_SIEMBRA:
                i = serie.indice(date(anio, mes, dia))
                if 0 <= i < len(serie.fechas):
                    filas.append((i, anio, mes, dia, (mes - 1) * len(DIAS_SIEMBRA) + DIAS_SIEMBRA.index(dia)))
    idx, anio, mes, dia, ranura = (np.array(c) for c in zip(*filas))
    return {'idx': idx, 'anio': anio, 'mes': mes, 'dia': dia, 'ranura': ranura}


def dia_365(fechas: np.ndarray) -> np.ndarray:
    """Día del año 0-364; el 29 de febrero cuenta como el 28 (igual que datos_tierra)."""
    anio = fechas.astype('datetime64[Y]')
    doy = (fechas - anio).astype(int)
    bisiesto = ((anio.astype(int) + 1970) % 4 == 0)
    return np.where(bisiesto & (doy >= 59), doy - 1, doy)


def climatologias_sin_anio(serie: Serie, variables=VARIABLES_ORACULO) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Media diaria por día del año dejando fuera cada año y el siguiente: {var: (n_anios, 365)}, suavizada a 15 días."""
    anios = serie.anios
    lista = np.unique(anios)
    doy = dia_365(serie.fechas)
    pos = np.searchsorted(lista, anios)
    nucleo = np.ones(VENTANA_CLIMA)
    salida = {}
    for var in variables:
        x = serie.v[var]
        ok = np.isfinite(x)
        suma = np.zeros((len(lista), 365))
        cuenta = np.zeros((len(lista), 365))
        np.add.at(suma, (pos[ok], doy[ok]), x[ok])
        np.add.at(cuenta, (pos[ok], doy[ok]), 1)
        # Ventana móvil circular sobre el día del año
        mitad = VENTANA_CLIMA // 2
        suma_v = np.stack([np.convolve(np.r_[s[-mitad:], s, s[:mitad]], nucleo, 'valid') for s in suma])
        cuenta_v = np.stack([np.convolve(np.r_[c[-mitad:], c, c[:mitad]], nucleo, 'valid') for c in cuenta])
        total, n_total = suma_v.sum(0), cuenta_v.sum(0)
        # El año siguiente (si existe) también sale: fila y resta y y y+1
        suma_fuera = suma_v + np.vstack([suma_v[1:], np.zeros((1, 365))])
        cuenta_fuera = cuenta_v + np.vstack([cuenta_v[1:], np.zeros((1, 365))])
        with np.errstate(invalid='ignore', divide='ignore'):
            salida[var] = (total - suma_fuera) / (n_total - cuenta_fuera)
    return lista, salida


def _serie_climatologica(anio: int, idx_anio: int, clim: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    fechas = np.arange(np.datetime64(f'{anio}-01-01'), np.datetime64(f'{anio + ANIOS_SERIE_CLIMA}-01-01'))
    doy = dia_365(fechas)
    return {var: valores[idx_anio][doy] for var, valores in clim.items()}


def taw_por_cultivo(serie: Serie, cultivos: Cultivos) -> np.ndarray:
    return np.array([agua_a_la_raiz(serie.suelo, zr)[0] for zr in cultivos.zr])


def frecuencia_sin_anio(exito: np.ndarray, anio: np.ndarray, ranura: np.ndarray) -> np.ndarray:
    """Para cada (siembra, cultivo): fracción de éxito en esa ranura del año en los demás años."""
    salida = np.full(exito.shape, np.nan)
    for r in np.unique(ranura):
        filas = np.where(ranura == r)[0]
        e = exito[filas]                              # (años, C)
        ok = np.isfinite(e)
        suma, n = np.where(ok, e, 0).sum(0), ok.sum(0)
        with np.errstate(invalid='ignore', divide='ignore'):
            salida[filas] = np.where(ok, (suma - e) / (n - 1), suma / n)
    return salida


def etiquetar(serie: Serie, cultivos: Cultivos) -> dict[str, np.ndarray]:
    """Devuelve columnas (S, C) de etiquetas reales y de línea base, más las fechas de siembra (S,)."""
    fechas = fechas_siembra(serie)
    taw = taw_por_cultivo(serie, cultivos)
    real = simulador.simular(serie.v, fechas['idx'], cultivos, taw)

    lista, clim = climatologias_sin_anio(serie)
    base = {k: np.full_like(v, np.nan) for k, v in real.items()}
    for anio in np.unique(fechas['anio']):
        filas = np.where(fechas['anio'] == anio)[0]
        v = _serie_climatologica(int(anio), int(np.searchsorted(lista, anio)), clim)
        inicio = np.datetime64(f'{anio}-01-01')
        idx_local = (serie.fechas[fechas['idx'][filas]] - inicio).astype(int)
        r = simulador.simular(v, idx_local, cultivos, taw)
        # Sin clima real después del fin de la serie, la línea base tampoco cuenta
        for k in base:
            base[k][filas] = np.where(np.isfinite(real['puntaje'][filas]), r[k], np.nan)

    salida = {**fechas, 'taw_mm': taw, **real, **{f'{k}_clim': v for k, v in base.items()}}
    salida['exito_frec_clim'] = frecuencia_sin_anio(real['exito'], fechas['anio'], fechas['ranura'])
    return salida
