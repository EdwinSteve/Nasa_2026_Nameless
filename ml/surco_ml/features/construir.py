"""Features del lote-fecha. El MISMO código sirve para entrenar y para la inferencia en el backend.

Regla sin fuga: todas las ventanas terminan el día ANTES de la siembra. La única información del
futuro es la climatología, y se calcula con los demás años (nunca con el año de la siembra).

Grupos (ml/README.md, sección 3): clima reciente de 30, 90 y 365 días; SMAP al sembrar y su
tendencia; IMERG; climatología de los próximos 90 y 210 días; ENSO; suelo; sitio y fecha.
"""
import numpy as np

from ..series import Serie

VENTANAS = (30, 90, 365)
VENTANAS_CLIMA = (90, 210)
# La climatología deja fuera el año de la siembra Y el siguiente: la piña (~525 días) y los
# perennes siguen en el campo al año siguiente, y esa ventana se cruzaría con su propio ciclo.
ANIOS_FUERA = (0, 1)
UMBRAL_DIA_LLUVIA_MM = 1.0
PROPIEDADES_SUELO = ('sand', 'silt', 'clay', 'soc', 'phh2o', 'cec', 'nitrogen', 'bdod', 'cfvo', 'wv0033', 'wv1500')
TRAMOS_SUELO = ('0-30cm', '0-100cm')


def _acumulada(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ok = np.isfinite(x)
    return np.r_[0.0, np.cumsum(np.where(ok, x, 0.0))], np.r_[0, np.cumsum(ok)]


def _media_ventana(cs, cn, s: np.ndarray, w: int, minimo: float = 0.8) -> np.ndarray:
    """Media de [s-w, s); NaN si hay menos del 80 % de días con dato o la ventana sale de la serie."""
    a = s - w
    valida = a >= 0
    a = np.clip(a, 0, None)
    n = cn[s] - cn[a]
    with np.errstate(invalid='ignore', divide='ignore'):
        media = (cs[s] - cs[a]) / n
    return np.where(valida & (n >= minimo * w), media, np.nan)


def _extremo_ventana(x: np.ndarray, s: np.ndarray, w: int, fn) -> np.ndarray:
    return np.array([fn(x[i - w:i]) if i - w >= 0 and np.isfinite(x[i - w:i]).any() else np.nan for i in s])


def clima_reciente(v: dict[str, np.ndarray], s: np.ndarray) -> dict[str, np.ndarray]:
    f = {}
    acum = {k: _acumulada(v[k]) for k in ('t', 'tmax', 'tmin', 'lluvia', 'hr', 'viento', 'radiacion', 'et0')}
    dias_lluvia = _acumulada((v['lluvia'] > UMBRAL_DIA_LLUVIA_MM).astype(float))
    for w in VENTANAS:
        m = {k: _media_ventana(*acum[k], s, w) for k in acum}
        f[f'f_t_media_{w}'] = m['t']
        f[f'f_tmax_media_{w}'] = m['tmax']
        f[f'f_tmin_media_{w}'] = m['tmin']
        f[f'f_lluvia_{w}'] = m['lluvia'] * w
        f[f'f_hr_{w}'] = m['hr']
        f[f'f_viento_{w}'] = m['viento']
        f[f'f_radiacion_{w}'] = m['radiacion']
        f[f'f_et0_{w}'] = m['et0'] * w
        f[f'f_balance_{w}'] = (m['lluvia'] - m['et0']) * w
        f[f'f_dias_lluvia_{w}'] = _media_ventana(*dias_lluvia, s, w) * w
        f[f'f_tmax_max_{w}'] = _extremo_ventana(v['tmax'], s, w, np.nanmax)
        f[f'f_tmin_min_{w}'] = _extremo_ventana(v['tmin'], s, w, np.nanmin)
    return f


def satelite(v: dict[str, np.ndarray], s: np.ndarray) -> dict[str, np.ndarray]:
    """SMAP (2015+) e IMERG (2000+): NaN antes de la misión, más una bandera de disponibilidad."""
    f = {}
    for k in ('sm_raiz', 'sm_superficie'):
        cs, cn = _acumulada(v[k])
        ahora = _media_ventana(cs, cn, s, 3, minimo=0.6)
        hace_30 = _media_ventana(cs, cn, np.clip(s - 30, 0, None), 7, minimo=0.6)
        f[f'f_{k}'] = ahora
        f[f'f_{k}_tendencia_30'] = ahora - np.where(s - 30 >= 7, hace_30, np.nan)
    f['f_smap_disponible'] = np.isfinite(f['f_sm_raiz']).astype(np.float64)
    cs, cn = _acumulada(v['imerg'])
    for w in (30, 90):
        f[f'f_imerg_{w}'] = _media_ventana(cs, cn, s, w, minimo=0.95) * w
    f['f_imerg_disponible'] = np.isfinite(f['f_imerg_90']).astype(np.float64)
    return f


def climatologia_futura(v: dict[str, np.ndarray], s: np.ndarray, anio: np.ndarray, ranura: np.ndarray) -> dict[str, np.ndarray]:
    """Media, p10 y p90 de los próximos 90 y 210 días en la MISMA fecha de los DEMÁS años.

    "Demás" excluye el año de la siembra y el siguiente (ANIOS_FUERA). Usa la lluvia de POWER
    (serie continua desde 1981) para que todos los años se comparen igual.
    """
    f = {}
    acum = {'t': _acumulada(v['t']), 'tmax': _acumulada(v['tmax']), 'lluvia': _acumulada(v['lluvia_power'])}
    n = len(v['t'])
    for w in VENTANAS_CLIMA:
        fin = s + w
        cabe = fin <= n
        fin_c = np.clip(fin, 0, n)
        agregados = {}
        for k, (cs, cn) in acum.items():
            with np.errstate(invalid='ignore', divide='ignore'):
                media = (cs[fin_c] - cs[s]) / (cn[fin_c] - cn[s])
            agregados[k] = np.where(cabe, media * (w if k == 'lluvia' else 1), np.nan)
        for k, real in agregados.items():
            media, p10, p90 = (np.full(len(s), np.nan) for _ in range(3))
            for r in np.unique(ranura):
                filas = np.where(ranura == r)[0]
                for i in filas:
                    fuera = np.isin(anio[filas] - anio[i], ANIOS_FUERA)
                    otros = real[filas[~fuera & np.isfinite(real[filas])]]
                    if len(otros) >= 5:
                        media[i] = otros.mean()
                        p10[i], p90[i] = np.percentile(otros, [10, 90])
            f[f'f_clim_{k}_{w}_media'] = media
            f[f'f_clim_{k}_{w}_p10'] = p10
            f[f'f_clim_{k}_{w}_p90'] = p90
    return f


def enso(serie: Serie, anio: np.ndarray, mes: np.ndarray) -> dict[str, np.ndarray]:
    """ONI del último trimestre COMPLETO antes de la siembra (centrado dos meses antes) y su tendencia."""
    oni = {(e['year'], e['month']): e['oni'] for e in serie.enso}

    def valor(a, m, atras):
        k = (a * 12 + (m - 1) - atras)
        return oni.get((k // 12, k % 12 + 1), np.nan)

    actual = np.array([valor(a, m, 2) for a, m in zip(anio, mes)])
    antes = np.array([valor(a, m, 5) for a, m in zip(anio, mes)])
    return {'f_oni': actual, 'f_oni_tendencia_3m': actual - antes}


def suelo_y_sitio(serie: Serie, n: int) -> dict[str, np.ndarray]:
    f = {}
    resumen = (serie.suelo or {}).get('summary', {})
    for tramo in TRAMOS_SUELO:
        for p in PROPIEDADES_SUELO:
            valor = resumen.get(tramo, {}).get(p, {}).get('Q0.5')
            f[f'f_suelo_{p}_{tramo.split("-")[1]}'] = np.full(n, np.nan if valor is None else valor)
    for p in ('clay', 'soc'):
        valor = resumen.get('0-30cm', {}).get(p, {}).get('rel_uncertainty')
        f[f'f_suelo_{p}_incertidumbre'] = np.full(n, np.nan if valor is None else valor)
    f['f_elevacion_m'] = np.full(n, serie.elevacion_m)
    f['f_lat'] = np.full(n, serie.lat)
    f['f_lon'] = np.full(n, serie.lon)
    f['f_desnivel_celda_m'] = np.full(n, serie.celda_power_m - serie.elevacion_m)
    return f


def fecha(serie: Serie, s: np.ndarray) -> dict[str, np.ndarray]:
    doy = (serie.fechas[s] - serie.fechas[s].astype('datetime64[Y]')).astype(int)
    angulo = 2 * np.pi * doy / 365.25
    return {'f_doy_sen': np.sin(angulo), 'f_doy_cos': np.cos(angulo)}


def construir(serie: Serie, siembras: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Una fila por fecha de siembra. siembras: salida de oraculo.etiquetas.fechas_siembra."""
    s = siembras['idx']
    return {
        **clima_reciente(serie.v, s),
        **satelite(serie.v, s),
        **climatologia_futura(serie.v, s, siembras['anio'], siembras['ranura']),
        **enso(serie, siembras['anio'], siembras['mes']),
        **suelo_y_sitio(serie, len(s)),
        **fecha(serie, s),
    }
